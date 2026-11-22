include $(TOPDIR)/rules.mk
PKG_NAME:=piefi-controller
PKG_VERSION:=0.2.0
PKG_RELEASE:=1
PKG_LICENSE:=MIT
include $(INCLUDE_DIR)/package.mk
define Package/piefi-controller
 SECTION:=utils
 CATEGORY:=Utilities
 TITLE:=PieFi experimental controller
 DEPENDS:=+python3-light +python3-sqlite3 +opennds +kmod-usb-serial
endef
define Build/Compile
endef
define Package/piefi-controller/install
 $(INSTALL_DIR) $(1)/usr/lib/piefi $(1)/etc/init.d $(1)/etc/config $(1)/www/piefi
 $(INSTALL_BIN) ./files/piefi.py $(1)/usr/lib/piefi/piefi.py
 $(INSTALL_BIN) ./files/coin_reader.py $(1)/usr/lib/piefi/coin_reader.py
 $(INSTALL_BIN) ./files/init $(1)/etc/init.d/piefi
 $(INSTALL_DATA) ./files/piefi.config $(1)/etc/config/piefi
 $(INSTALL_DATA) ./files/dashboard.html $(1)/www/piefi/index.html
endef
$(eval $(call BuildPackage,piefi-controller))
