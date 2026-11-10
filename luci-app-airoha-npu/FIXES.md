# 修复说明 / Fix notes

本目录是修复后的完整源码，版本 1.0.2。以下两个问题的原因和改动都可以逐条复核。

## 一、`ERROR: please fix feeds/npu/luci-app-airoha-npu/luci-app-airoha-npu/Makefile`

### 原因

OpenWrt 的 `scripts/feeds` 不按包名找包，而是用
`include/scan.mk` 在 feed 目录下 `find -name Makefile -maxdepth 5`，把找到的
每一个 Makefile 都当成一个包去执行 `make -r DUMP=1 -C <目录>`：

```
find -L feeds/npu -mindepth 1 -maxdepth 5 -name Makefile | xargs grep -aHE 'call (BuildPackage|...)'
```

旧仓库里除了顶层的包，还留着一份 2026 年 4 月旧目录结构下的**整份副本**：

```
luci-app-airoha-npu/
├── Makefile                 <- 正确的包
├── htdocs/ root/ po/ ...
└── luci-app-airoha-npu/     <- 旧副本（残留）
    ├── Makefile             <- include ../../luci.mk
    ├── htdocs/ po/ root/ ...
```

作为 feed 安装后，这份副本位于
`feeds/npu/luci-app-airoha-npu/luci-app-airoha-npu/`，它的
`include ../../luci.mk` 会上溯到 `feeds/npu/luci.mk`；该文件不存在（真正的位置是
`feeds/luci/luci.mk`），于是 `make` 求值失败，`scan.mk` 打印上面那条错误，并把
`feeds/npu.index` 删掉。

另外，这份副本与顶层的包同名（也叫 `luci-app-airoha-npu`），且缺少
`root/usr/share/rpcd/acl.d/`、`status.js` 也是旧版，一旦被选中就会覆盖新版文件：
菜单能点开但页面报无权限、文案回退英文，都和它有关。

### 改动

* 删除 `luci-app-airoha-npu/luci-app-airoha-npu/` 整份残留副本。
* 顶层 `Makefile` 里加注释说明「本目录就是包本身，不要再套一层」。
* `.github/workflows/build.yml` 原来 `cp -R /opt/alist/luci-app-airoha-npu .`
  复制的正是这份旧副本，已改为把整个检出内容放进 `package/luci-app-airoha-npu`。

### 复核

```sh
# 1. 只剩一个 Makefile，且就在 feed 的第一层
find -L feeds/npu -name Makefile
# feeds/npu/luci-app-airoha-npu/Makefile

# 2. 它引用的 luci.mk 确实存在
grep -n 'luci.mk' feeds/npu/luci-app-airoha-npu/Makefile
grep -n 'call BuildPackage' feeds/npu/luci-app-airoha-npu/Makefile

# 3. 重新生成索引，不再出现 ERROR
./scripts/feeds update -a
./scripts/feeds install luci-app-airoha-npu     # Installing package 'luci-app-airoha-npu' from npu
make package/luci-app-airoha-npu/compile V=s
```

## 二、语言丢失（中文界面变成英文、部分词条永远是英文）

### 原因

1. **没有中文目录**：`po/` 下只有 `es/` 和 `templates/`。`luci.mk` 的语言列表是
   `LUCI_LANGUAGES := $(sort $(filter-out templates,$(notdir $(wildcard ${CURDIR}/po/*))))`，
   没有 `po/zh_Hans`，就既不会生成 `luci-i18n-airoha-npu-zh_Hans` 包，也不会编译
   中文 `.lmo`，页面只能回退英文。
2. **语言包和主程序是两个包**：`luci.mk` 为每种语言生成 `luci-i18n-airoha-npu-<lang>`，
   它才是安装 `/usr/lib/lua/luci/i18n/luci-app-airoha-npu.<lang>.lmo` 的包。只装
   `luci-app-airoha-npu` 时，菜单、页面标题、ACL 描述都还是英文——这是最容易
   被当成「语言丢了」的情况。
3. **三条词条对不上**：`status.js` 里 `_('Bound ')`、`_('Total ')`、`_('Manages: ')`
   带尾随空格，`.po` 里是 `Bound`、`Total`、`Manages:`，运行时查不到译文，
   任何语言下都显示英文。
4. **模板与视图中英不一致**：`po/templates/*.pot` 还是按旧版视图（旧目录结构、
   `Bound:`/`CPU set to`/`Must be 500-1600 MHz` 等）生成的，`es` 里 77 条有 47 条
   `msgstr` 为空，`#:` 注释指向 `feeds/luci/applications/...`。
5. **CI 打包打的是旧副本**（见上一节），所以 release 里的 ipk 连 `acl.d` 和
   新版视图都没有。

### 改动

* 新增 `po/zh_Hans/luci-app-airoha-npu.po`：77 条（视图 75 条 + 菜单标题
  `SoC Status` + ACL 描述）全部翻译，`Language: zh_Hans`，`nplurals=1; plural=0;`。
  `luci.mk` 会因此生成 `luci-i18n-airoha-npu-zh_Hans`，安装
  `luci-app-airoha-npu.zh-cn.lmo`（`zh_Hans` 的 aliases 是 `zh-cn`）。
* 补齐 `po/es/luci-app-airoha-npu.po`：采用社区 PR #6（castillofrancodamian）的
  西语译文，77 条全部有译文（原来 47 条为空），并去掉已失效的旧词条。
* 重新生成 `po/templates/luci-app-airoha-npu.pot`：以 `status.js` 里实际的
  `_()` 字面量为准，加上 menu.d / acl.d 两条，`#:` 指向本包路径。
* `status.js`：把 `_('Bound ')`、`_('Total ')`、`_('Manages: ')` 的尾随空格改到
  `style="margin-right:4px"`，词条与模板对齐，三种语言都能命中。
* 三个 `.po`/`.pot` 均为 UTF-8、`Content-Type: text/plain; charset=UTF-8`，
  可以直接被 `po2lmo` 编译，无遗留的 `#~` 失效条目。

### 复核

```sh
# 语言目录与包名
ls po/
# es  templates  zh_Hans

# 词条数：三个文件都应是 78（77 条词条 + 1 条头部空 msgid）
grep -c '^msgid "' po/templates/luci-app-airoha-npu.pot
grep -c '^msgid "' po/es/luci-app-airoha-npu.po
grep -c '^msgid "' po/zh_Hans/luci-app-airoha-npu.po
# 空译文只允许出现在头部：pot 全部为空是正常的，po 里只应有 1 条
grep -c '^msgstr ""$' po/zh_Hans/luci-app-airoha-npu.po

# 编译语言包（luci.mk 自动创建这些目标）
make package/luci-app-airoha-npu/compile V=s
find bin/packages -name 'luci-i18n-airoha-npu-*.ipk'
```

路由器上：

```sh
opkg install luci-i18n-airoha-npu-zh_Hans_*.ipk
# 系统 -> 系统 -> 语言和界面 选「简体中文」，保存并应用后重新登录
```

## 改动文件清单

| 文件 | 改动 |
|------|------|
| `luci-app-airoha-npu/`（副本） | 删除 |
| `Makefile` | 版本 1.0.2-r1，说明目录即包本身 |
| `htdocs/.../status.js` | 3 处词条去掉尾随空格 |
| `po/templates/luci-app-airoha-npu.pot` | 按实际视图重新生成，77 条 |
| `po/es/luci-app-airoha-npu.po` | 补齐到 77 条，清理失效词条 |
| `po/zh_Hans/luci-app-airoha-npu.po` | 新增，77 条全译 |
| `README.md` | 安装/feed/语言包说明，版本历史 |
| `.github/workflows/build.yml` | 复制整个检出目录，附带编译语言包 |
| `FIXES.md` | 本文件 |

---

## English summary

* The feed error came from a stale duplicate package tree at
  `luci-app-airoha-npu/luci-app-airoha-npu/`. `include/scan.mk` walks every
  `Makefile` up to five levels deep, and that copy's `include ../../luci.mk`
  resolves to `feeds/npu/luci.mk`, which does not exist. It is removed.
* Translations were lost because there was no `po/zh_Hans` catalog at all, the
  catalogs were out of date with the view (47 of 77 Spanish strings empty), and
  three msgids carried a trailing space (`'Bound '`, `'Total '`, `'Manages: '`)
  so they could never match. All four are fixed; `es` and `zh_Hans` now cover
  every string the page renders, and the `.pot` is regenerated from the view.
* Translations still ship as separate `luci-i18n-airoha-npu-<lang>` packages
  built by `luci.mk` from `po/<lang>/`; install the one for your language
  alongside `luci-app-airoha-npu`.
