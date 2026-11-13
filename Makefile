# This is free software, licensed under the Apache License, Version 2.0 .

# The repository root is the package itself: Makefile, htdocs/, root/ and po/
# all live at the top level, so the checkout is cloned straight into
# package/luci-app-airoha-npu or used as a src-link feed entry.
#
# Do not nest another luci-app-airoha-npu/ directory below this one.
# include/scan.mk treats every Makefile up to five directory levels deep as a
# package of its own, so a nested copy is scanned as a second package with the
# same name: its stale files shadow this one and a bad `include` in it aborts
# the feed scan with "please fix .../Makefile".

include $(TOPDIR)/rules.mk

PKG_VERSION:=1.0.2
PKG_RELEASE:=1

PKG_LICENSE:=Apache-2.0
PKG_LICENSE_FILES:=LICENSE

LUCI_TITLE:=LuCI Airoha SoC Status (NPU, CPU, Frame Engine)
LUCI_MAINTAINER:=Ryan Chen <rchen14b@gmail.com>
LUCI_URL:=https://github.com/rchen14b/luci-app-airoha-npu
LUCI_DESCRIPTION:=Status page for Airoha EN7581 and AN7583 SoCs: NPU state and \
	reserved memory, the Frame Engine port counters and PSE queues, the PPE \
	flow offload table, plus CPU frequency, governor and direct PLL overclock. \
	The Frame Engine section and the overclock control read and write registers \
	through the busybox devmem applet (CONFIG_BUSYBOX_CONFIG_DEVMEM), which is \
	not enabled in a default build; without it the rest of the page still works. \
	The PPE table needs CONFIG_KERNEL_DEBUG_FS and the WiFi queue view needs the \
	mt76 debugfs nodes.
LUCI_DEPENDS:=+luci-base @TARGET_airoha

include $(TOPDIR)/feeds/luci/luci.mk

# call BuildPackage - OpenWrt buildroot signature
