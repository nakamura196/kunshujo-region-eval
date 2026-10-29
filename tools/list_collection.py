"""確認 5: 図書館の田中芳男コレクションページ（捃拾帖）の一覧を全ページ取り、帖名を並べる。
    python3 tools/kunshujo/list_collection.py <出力TSV>
"""
import re, sys, time, urllib.request, html
U = 'https://da.dl.itc.u-tokyo.ac.jp/portal/collection/ac164701-8637-4ebe-65fa-fcd8427f52d9'
seen = {}; p = 0
while p < 60:
    t = urllib.request.urlopen(f'{U}?page={p}', timeout=60).read().decode()
    items = re.findall(r'<h3 class="media-heading ">\s*<a href="/portal/assets/([0-9a-f-]+)"[^>]*>\s*<span>([^<]+?)</span>', t)
    new = [(i, html.unescape(n)) for i, n in items if i not in seen]
    if not new: break
    for i, n in new: seen[i] = n
    p += 1; time.sleep(0.5)
open(sys.argv[1], 'w').write(''.join(f'{i}\t{n}\n' for i, n in seen.items()))
print('pages', p, 'items', len(seen))
