import asyncio
import json
import logging
import os
from typing import List, Callable, Dict

import aiofiles
import aiohttp
import packageurl
import psutil
import smart_open
from aiohttp_retry import RetryClient, ExponentialRetry
from lxml import etree

from file_helper import resolve_archive
from requirements_detector.methods import from_setup_cfg, from_setup_py, from_requirements_txt, from_pyproject_toml
from requirements_detector.requirement import DetectedRequirement
from util import spider, ensure_dir, spider_async

office_url = 'https://pypi.org/simple'
tsinghua_url = 'https://pypi.tuna.tsinghua.edu.cn/simple'
aliyun_url = 'https://mirrors.aliyun.com/pypi/simple/'
base_url = tsinghua_url

FILE_SETUP_PY = 'setup.py'
FILE_SETUP_CFG = 'setup.cfg'
FILE_REQUIRES = 'requires.txt'
FILE_PYPROJECT = 'pyproject.toml'

PY_PARSE_MAP: Dict[str, Callable[[str], List[DetectedRequirement]]] = {
    FILE_SETUP_PY: from_setup_py,
    FILE_SETUP_CFG: from_setup_cfg,
    FILE_REQUIRES: from_requirements_txt,
    FILE_PYPROJECT: from_pyproject_toml,
}


def is_zip(s):
    return s.endswith('zip') or s.endswith('egg')


def is_tar(s):
    return s.endswith('tar.gz') or s.endswith('tar.bz2')


def safe_get(j, k, default):
    v = j.get(k, default)
    if v is None:
        return default
    return v


def to_json_without_none(d: Dict) -> str:
    def del_none(d: Dict) -> Dict:
        for key, value in list(d.items()):
            if not value:
                # 删除空值
                del d[key]
            elif value in ('UNKNOWN', 'Unknown'):
                # 删除魔数
                del d[key]
            elif isinstance(value, dict):
                del_none(value)
        return d

    return json.dumps(del_none(d))


# 获得包名索引
def get_packages_list(file: str) -> List[Dict]:
    """
    从本地文件加载包列表

    Args:
        file: 包索引文件路径

    Returns:
        包信息列表

    Raises:
        FileNotFoundError: 当包索引文件不存在时抛出
    """
    if not os.path.exists(file):
        raise FileNotFoundError(f"Package index file {file} not found.")

    packages_list = []
    with open(file, 'r') as f:
        for line in f:
            packages_list.append(json.loads(line.strip()))
    return packages_list


# 协程方式爬取包主页，收集各版本包url
async def get_releases_by_coroutine(package: str, limit: asyncio.Semaphore, output: str):
    """
    异步获取指定Python包的最新发布版本信息

    Args:
        package: 包名称
        limit: 并发限制信号量
        output: 输出文件路径
    """
    async with limit:
        try:
            result = await spider_async(f'https://pypi.org/pypi/{package}/json')
            # 根据实际返回结构调整
            if isinstance(result, tuple) and len(result) >= 2:
                meta, response_info = result
                # 如果response_info是headers，需要从中提取状态码
                if hasattr(response_info, 'status'):  # aiohttp response对象
                    status = response_info.status
                elif isinstance(response_info, int):  # 直接的状态码
                    status = response_info
                else:
                    status = 200  # 默认成功
            else:
                meta = result
                status = 200
            if status != 200:
                logging.warning(f"[Releases] Failed to fetch metadata for {package}, status: {status}")
                return

            meta = json.loads(meta)

            # 只获取最新版本
            latest_version = meta.get('info', {}).get('version')
            releases_data = meta.get('releases', {})

            if latest_version and latest_version in releases_data:
                latest_release = releases_data[latest_version]
                if len(latest_release) > 0:
                    release_entry = {
                        'purl': packageurl.PackageURL(type='pypi', name=package, version=latest_version).to_string(),
                        'artifact': package,
                        'version': latest_version,
                        'url': sorted(list(map(lambda x: x.get('url'), latest_release)),
                                      key=lambda url: (
                                          url.endswith('tar.gz'),
                                          url.endswith('tar.bz2'),
                                          url.endswith('zip'),
                                          url.endswith('egg'),
                                      ), reverse=True)[0],
                        'createTime': latest_release[0].get('upload_time_iso_8601'),
                    }

                    # 写入文件
                    async with aiofiles.open(output, 'a') as f:
                        await f.write('{}\n'.format(to_json_without_none(release_entry)))
            else:
                logging.warning(f"[Releases] No release data found for {package} latest version {latest_version}")

        except Exception as e:
            logging.error(f'[Deps] fail to get releases for package: {package}, err: {e}')


# 协程方式爬取每个包
async def get_archive_by_coroutine(url: str, package: str, edition: str, limit: asyncio.Semaphore, output: str):
    """
    异步下载并分析Python包归档文件的依赖关系

    Args:
        url: 包文件下载链接
        package: 包名称
        edition: 版本号
        limit: 并发限制信号量
        output: 输出文件路径
    """
    try:
        async with limit:
            reqs = set()
            async with RetryClient(aiohttp.ClientSession(), retry_options=ExponentialRetry()) as session:
                async with session.get(url) as res:
                    if res.status == 404:
                        return
                    size = res.headers.get('Content-Length')
                    if size is not None and (
                            int(size) > 1024 * 1024 * 100 or
                            psutil.virtual_memory().available - 500 * 1024 * 1024 < int(size)
                    ):
                        logging.warning(
                            f'[Deps] skip huge file, url: {url}, size: {int(size) / 1024 / 1024} MB, available: {psutil.virtual_memory().available / 1024 / 1024} MB')
                        return
                    archive = resolve_archive(await res.read())
                    if not archive:
                        logging.warning(f'[Deps] illegal archive: {url}')
                        return
                    reqs = set()

                    def dep(name: str):
                        # 过滤掉隐藏文件和非Python相关文件
                        if name.startswith('.') or name.startswith('_'):
                            return
                        # 只处理我们关心的配置文件
                        for k in PY_PARSE_MAP:
                            if name.endswith(k):
                                try:
                                    file_content = archive.get_file_by_name(name)
                                    if file_content:
                                        decoded_content = file_content.decode('utf-8')
                                        k_reqs = PY_PARSE_MAP[k](decoded_content)
                                        reqs.update(k_reqs)
                                except UnicodeDecodeError as e:
                                    logging.warning(
                                        f'[Deps] fail to decode deps file: {package}-{edition}.{name}, url: {url}, err: {e}')
                                except Exception as e:
                                    logging.warning(
                                        f'[Deps] fail to parse deps file: {package}-{edition}.{name}, url: {url}, err: {e}')
                                return

                    archive.iter(dep)
            async with aiofiles.open(output, 'a') as f:
                content = '{},{},,,\n'.format(package, edition)
                if len(reqs):
                    content = ''
                    for req in reqs:
                        if len(req.version_specs) == 0:
                            content += '{},{},{},,\n'.format(package, edition, req.name)
                        for v in req.version_specs:
                            content += '{},{},{},{},{}\n'.format(package, edition, req.name, v[1], v[0])
                await f.write(content)
    except Exception as e:
        logging.error(f'[Deps] fail to parse deps for release: {package}-{edition}, url: {url}, err: {e}')



def standardize(name: str) -> str:
    return name.lower().replace('_', '-')


if __name__ == '__main__':
    # 准备工作目录
    dir = 'python/pypi'
    ensure_dir(dir)

    # 准备文件
    logging.basicConfig(filename=f'{dir}/python-deps-2024-06-27.log', level=logging.INFO)
    deps_file = f'{dir}/pypi_v10.csv'
    packages_file = f'{dir}/packages-2024-06-27.txt'
    releases_file = f'{dir}/releases-2025-12-16.txt'

    # 设置事件循环 (兼容Python 3.10+)
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # 设置并发数
    limit = asyncio.Semaphore(20)

    # 获取包名列表（从已有文件）
    packages = get_packages_list(packages_file)
    logging.info(f'finish fetching packages list, size = {len(packages)}')

    # 如果还没有获取每个包的所有版本，则执行此步骤
    if os.path.exists(releases_file):
        # 协程获取每个包的所有版本
        loop.run_until_complete(asyncio.wait(list(
            map(lambda p: loop.create_task(get_releases_by_coroutine(p.get('artifact'), limit, releases_file)),
                packages))))
        logging.info(f'finish fetching releases')

    # 协程解析每个版本的依赖
    v = 0
    flag = True
    # 在主程序的JSON解析部分添加异常处理
    while flag:
        with open(releases_file, 'r') as f:
            # 跳过已处理的行
            for i in range(0, v):
                f.readline()
            # 每次处理10000行
            tasks = []
            for i in range(0, 10000):
                line = f.readline().strip()
                # 读到文件结尾，提前跳出
                if len(line) == 0:
                    flag = False
                    break
                # 记录处理行数
                v += 1
                try:
                    release = json.loads(line)
                    url = release.get('url')
                    if is_tar(url) or is_zip(url):
                        # 使用镜像源提高下载速度
                        url = url.replace('https://files.pythonhosted.org/', 'https://pypi.tuna.tsinghua.edu.cn/')
                        tasks.append(loop.create_task(get_archive_by_coroutine(
                            url, release.get('artifact'), release.get('version'), limit, deps_file)))
                except json.JSONDecodeError as e:
                    logging.warning(f"Invalid JSON line skipped: {line[:50]}... Error: {e}")
                    continue
            if tasks:
                loop.run_until_complete(asyncio.wait(tasks))
            logging.info('processed {} releases'.format(v))


