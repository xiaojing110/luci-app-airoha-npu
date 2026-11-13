# 修复说明 / Fix notes

本仓库是修复后的完整源码，版本 1.0.2。下面每一条都写了原因、改动和复核方法。

---

## 一、插件目录：仓库里还留着一整份旧的包副本

### 原因

OpenWrt 的 `scripts/feeds` 不按包名找包，而是用 `include/scan.mk` 在 feed
目录下 `find -name Makefile -maxdepth 5`，把找到的每一个 Makefile 都当成一个包
去执行：

```
find -L feeds/npu -mindepth 1 -maxdepth 5 -name Makefile | xargs grep -aHE 'call (BuildPackage|...)'
```

旧仓库里除了顶层的包，还留着一份旧目录结构下的**整份副本**：

```
luci-app-airoha-npu/
├── Makefile                 <- 真正的包
├── htdocs/ root/ po/ ...
└── luci-app-airoha-npu/     <- 残留副本
    ├── Makefile             <- include ../../luci.mk
    └── htdocs/ po/ root/ ...
```

作为 feed 安装后，副本位于 `feeds/npu/luci-app-airoha-npu/luci-app-airoha-npu/`，
它的 `include ../../luci.mk` 会上溯到 `feeds/npu/luci.mk`（不存在，真正的位置是
`feeds/luci/luci.mk`），于是报
`ERROR: please fix feeds/npu/luci-app-airoha-npu/luci-app-airoha-npu/Makefile`
并删掉 `feeds/npu.index`。

副本和顶层包**同名**，且缺 `root/usr/share/rpcd/acl.d/`、`status.js` 也是旧版。
即使扫描没报错，一旦它被选中就会覆盖新版文件：菜单点得开但页面报无权限、文案
回退英文，都和它有关。

### 改动

* 删除 `luci-app-airoha-npu/luci-app-airoha-npu/` 整份副本。仓库根目录**就是**
  包本身，`Makefile`、`htdocs/`、`root/`、`po/` 都在第一层。
* 顶层 `Makefile` 开头写明这一点：不要再套一层，否则会被扫描成同名第二个包。
* `.github/workflows/build.yml` 原来 `cp -R /opt/alist/luci-app-airoha-npu .`
  复制的正是这份副本，已改为把整个检出目录放进 `package/luci-app-airoha-npu`。

### 复核

```sh
# 1. 只剩一个 Makefile，且就在第一层
find . -name Makefile
# ./Makefile

# 2. 它引用的 luci.mk 确实存在，并且调用了 BuildPackage
grep -n 'luci.mk\|BuildPackage' Makefile

# 3. 作为 feed 重新扫描，不再出现 ERROR
./scripts/feeds update -a
./scripts/feeds install luci-app-airoha-npu
make package/luci-app-airoha-npu/compile V=s
```

---

## 二、中文语言文件：`po/zh_Hans` 缺失

### 原因

1. **没有中文目录**。`luci.mk` 的语言列表是
   `LUCI_LANGUAGES := $(sort $(filter-out templates,$(notdir $(wildcard ${CURDIR}/po/*))))`，
   `po/` 下只有 `es/` 和 `templates/` 时，既不会生成中文语言包，也不会编译
   `zh-cn.lmo`，页面只能回退英文。
2. **语言包和主程序是两个包**。`luci.mk` 为每种语言生成
   `luci-i18n-airoha-npu-<别名>`，它才是安装
   `/usr/lib/lua/luci/i18n/luci-app-airoha-npu.<别名>.lmo` 的包。只装
   `luci-app-airoha-npu` 时，菜单、页面标题、ACL 描述都还是英文——这是最常被
   当成「语言丢了」的情况。
3. **别名是 `zh-cn`，不是 `zh_Hans`**。`luci.mk` 里
   `LUCI_LC_ALIAS.zh_Hans=zh-cn`，包名取别名，所以语言包叫
   **`luci-i18n-airoha-npu-zh-cn`**，装出来的文件是
   `luci-app-airoha-npu.zh-cn.lmo`。目录名仍是 `po/zh_Hans/`。
   写 `opkg install luci-i18n-airoha-npu-zh_Hans` 会找不到包。
4. **三条词条对不上**。`status.js` 里 `_('Bound ')`、`_('Total ')`、
   `_('Manages: ')` 带尾随空格，`.po` 里是 `Bound`、`Total`、`Manages:`，
   运行时查不到译文，**任何语言**下都显示英文。
5. **模板与视图不一致**。`po/templates/*.pot` 是按旧版视图生成的，`#:` 指向
   `feeds/luci/applications/...`；`es` 里 77 条有 50 条 `msgstr` 为空，还留着
   一堆 `#~` 失效词条。

### 改动

* 新增 `po/zh_Hans/luci-app-airoha-npu.po`：77 条（视图 75 条 + 菜单标题
  `SoC Status` + ACL 描述）全部翻译，`Language: zh_Hans`，
  `nplurals=1; plural=0;`。`luci.mk` 会因此生成
  `luci-i18n-airoha-npu-zh-cn`。
* 补齐 `po/es/luci-app-airoha-npu.po`：77 条全部有译文，去掉全部 `#~` 失效
  词条，补上 `Plural-Forms: nplurals=2; plural=(n != 1);`。
* 重新生成 `po/templates/luci-app-airoha-npu.pot`：以 `status.js` 里实际的
  `_()` 字面量为准，加上 menu.d / acl.d 两条，`#:` 指向本包路径，保持 LuCI
  模板用的 `msgstr "Content-Type: text/plain; charset=UTF-8"` 单行头。
* `status.js`：把三处尾随空格从词条里去掉，间距改用
  `style="margin-right:4px"`，词条与模板对齐，三种语言都能命中。
* 三个文件均为 UTF-8、LF、无 BOM，`%d`/`%s` 占位符与 `msgid` 一一对应。
* 新增 `scripts/gen-po.py`：从视图、menu.d、acl.d 重新生成并校验三个文件
  （`--check` 与 CI 用的是同一套检查）。

### 关于 `%%`

`'%d used / %d free (%s%%)'`、`'HW Offload: %s%%'` 里的 `%%` 是**对的**，不要
改成单个 `%`：LuCI 的 `String.prototype.format`（`cbi.js`，照抄 Lua 的
`string.format`）用 `(%|b|c|d|u|f|o|s|x|X|q|h|j|t|m)` 匹配转换符，`%%` 输出
一个字面 `%`。

### 复核

```sh
# 语言目录与包名
ls po/
# es  templates  zh_Hans

# 三个文件都应是 77 条词条 + 1 条头部
grep -c '^msgid "' po/templates/luci-app-airoha-npu.pot
grep -c '^msgid "' po/es/luci-app-airoha-npu.po
grep -c '^msgid "' po/zh_Hans/luci-app-airoha-npu.po

# 没有空译文、没有失效词条、占位符一致（CI 也是这条）
python3 scripts/gen-po.py --check

# 编译语言包（luci.mk 自动创建这些目标）
make package/luci-app-airoha-npu/compile V=s
find bin/packages -name 'luci-i18n-airoha-npu-*.ipk'
# luci-i18n-airoha-npu-zh-cn_*.ipk  luci-i18n-airoha-npu-es_*.ipk
```

路由器上：

```sh
opkg install luci-app-airoha-npu_*.ipk luci-i18n-airoha-npu-zh-cn_*.ipk
# 系统 -> 系统 -> 语言和界面 选「简体中文」，保存并应用后重新登录
```

---

## 三、其他隐藏问题

| 问题 | 说明 | 改动 |
|------|------|------|
| CI 编译的 SDK 目标不对 | `build.yml` 用 `rockchip/armv8` + 22.03.5，而包依赖 `@TARGET_airoha`。目标不匹配时这个包在 menuconfig 里根本不可选，CI 永远编不出来 | 换成 airoha 快照 SDK，`an7581` 和 `an7583` **两个子目标矩阵各编一次**（`@TARGET_airoha` 是 target 级依赖，两个子目标都满足），三个包都是 `Architecture: all`，发布时合并去重只发一份 |
| CI 克隆的是别人的仓库 | `git clone https://github.com/h70076000/luci-app-airoha-npu.git`，编的不是当前提交 | 改成 `actions/checkout` |
| CI 不编译语言包 | 只跑 `make package/luci-app-airoha-npu/compile`，i18n 包默认隐藏、不会被选 | `.config` 里打开 `CONFIG_LUCI_LANG_zh_Hans` / `_es`，并显式编译两个 i18n 目标 |
| 发布产物名写死 | `mv *.ipk luci-app-airoha-npu_all.ipk` 会把语言包也并成一个名字 | 用 `find` 收集所有 `*airoha-npu*.ipk` 上传 |
| `grep -c … \|\| echo 0` 的写法 | `grep -c` 即使 0 匹配也会打印 `0` 并以 1 退出，`\|\| echo 0` 于是把它变成 `0\n0`；这个值随后被 `printf %d` 塞进 JSON，可能直接让 `getStatus` 返回非法 JSON | `luci.airoha_npu` 里去掉多余的 `echo 0` |
| CRLF 会让 rpcd 脚本失效 | `.gitattributes` 只有 `* text=auto`，Windows 上检出后 `luci.airoha_npu` 的 shebang 会带 CR，路由器上跑不起来 | 对 `Makefile`、rpcd 脚本、`*.js/*.json/*.po/*.pot/*.yml` 显式 `eol=lf` |
| 版本没动 | 内容变了但仍是 1.0.1-r2，opkg 不会升级 | `PKG_VERSION:=1.0.2`，`PKG_RELEASE:=1` |
| README 版本/结构过期 | 徽章写 1.0.1，目录树里没有 `po/`、`scripts/`，也没说语言包是独立包 | 同步更新，补「Translations」一节 |

---

## 改动文件清单

| 文件 | 改动 |
|------|------|
| `luci-app-airoha-npu/luci-app-airoha-npu/` | 删除整份残留副本 |
| `Makefile` | 1.0.2-r1，说明目录即包本身、不要再套一层 |
| `htdocs/.../status.js` | 3 处词条去掉尾随空格，间距改到 style |
| `po/templates/luci-app-airoha-npu.pot` | 按实际视图重新生成，77 条，引用指向本包 |
| `po/es/luci-app-airoha-npu.po` | 补齐到 77 条，清理 `#~` 失效词条，加 `Plural-Forms` |
| `po/zh_Hans/luci-app-airoha-npu.po` | 新增，77 条全译 |
| `scripts/gen-po.py` | 新增，生成 + 校验语言文件 |
| `root/usr/libexec/rpcd/luci.airoha_npu` | 去掉会让 JSON 变形的 `echo 0` 备用分支 |
| `.gitattributes` | 关键文件强制 LF |
| `.github/workflows/build.yml` | airoha 两个子目标（an7581/an7583）矩阵编译、编译当前提交、带上语言包、校验语言文件、合并发布 |
| `README.md` | 语言包安装说明、目录结构、1.0.2 版本记录 |
| `FIXES.md` | 本文件 |

---

## English summary

* **Duplicate package tree removed.** `luci-app-airoha-npu/luci-app-airoha-npu/`
  was a stale full copy of the package. `include/scan.mk` walks every Makefile
  up to five levels deep, so that copy was scanned as a second package of the
  same name; its `include ../../luci.mk` resolved to `feeds/npu/luci.mk`, which
  does not exist, which aborted the feed scan, and it shadowed the real files
  (no `acl.d`, older view).
* **Chinese catalog added.** There was no `po/zh_Hans` at all, so `luci.mk` never
  generated the `luci-i18n-airoha-npu-zh-cn` package (the alias for `zh_Hans` is
  `zh-cn`) and no `zh-cn.lmo` was ever built. It now covers all 77 strings.
* **Three msgids could never match.** `'Bound '`, `'Total '` and `'Manages: '`
  carried a trailing space the catalogs did not; the space moved to CSS.
* **Catalogs resynchronised.** `es` is complete (50 of 77 were empty) and free of
  `#~` entries, and the `.pot` is regenerated from the view with correct
  references. `scripts/gen-po.py --check` (also run by CI) fails on any missing,
  stale or empty entry or on a format-specifier mismatch.
* **CI fixed.** It used a rockchip 22.03.5 SDK for a package that depends on
  `@TARGET_airoha` (never selectable), cloned a third-party fork instead of the
  commit under test, and never built the language packages. It now builds in a
  matrix over both airoha subtargets — `an7581` **and** `an7583`, since the page
  supports both SoCs — copies this checkout, enables
  `CONFIG_LUCI_LANG_zh_Hans` and `_es`, and a final job merges the two artifact
  sets and publishes all three ipk files. They are `Architecture: all`, so the
  merged duplicate names collapse into a single copy that fits either SoC.
* **Smaller fixes.** `.gitattributes` pins LF for the shell script and catalogs,
  the `grep -c … || echo 0` that produced `0\n0` for `printf %d` is gone, and the
  version is bumped to 1.0.2.
