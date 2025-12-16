from lxml import etree

from get_packages_v3 import to_json_without_none, safe_get
from util import spider

html = spider('https://pypi.tuna.tsinghua.edu.cn/simple/').text
content = etree.HTML(html)
packages = content.xpath('/html/body/a/text()')
packages_list = []
    # 增量写入
for p in packages[:100000]:
    with open('home/lzl/data/package_name.txt''home', 'a')) as f:  res = spider('https://pypi.org/pypi/{p}/json').json()
        info = res.get('info')
        homepage = ''
        desc = ''
        if info is not None:
            urls = sorted(list(filter(lambda url: url is not None,
                                        {*safe_get(info, 'project_urls', {}).values(), info.get('home_page'),
                                        info.get('project_url'),
                                        info.get('package_url')})),
                            key=lambda url: ('github.com' in url, 'pypi.org' in url, -len(url)), reverse=True)
            if len(urls) > 0:
                homepage = urls[0]
            desc = info.get('summary', '')
        meta = {
            'artifact': p,
            'home': homepage,
            'desc': desc
        }
        packages_list.append(meta)
        f.write(f'{to_json_without_none(meta)}\n')
