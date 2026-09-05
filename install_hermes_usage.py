#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hermes-usage  单文件安装器 (Token 用量: Hermes 底部实时用量条 + /usage 历史详情页)

在一台已安装 Hermes 的机器上运行即可直接使用:

    方式A(完整版,含历史详情页,推荐):    python install_hermes_usage.py
    方式B(仅底部用量条,免改配置,零依赖): python install_hermes_usage.py --bar-only

自动探测 Hermes 数据目录(HERMES_HOME)并按需写入:
    <home>/desktop-plugins/hermes-usage/plugin.js
    <home>/plugins/hermes-usage/dashboard/{manifest.json,plugin_api.py}
并把插件加入 config.yaml 的 plugins.enabled(会先备份 config.yaml.bak-hermes-usage)。

安装后: 彻底退出 Hermes 桌面端(含托盘)再打开; 若底部条没出现,
按 Ctrl+K 输入 Reload desktop plugins 回车。数据来自 Hermes 自带的
state.db(session_model_usage), 不拦截、不改库。
"""
import base64
import os
import sys
from pathlib import Path

__version__ = "0.2.0"

B64_desktop_plugins_hermes_usage_plugin_js = (
        "LyoqCiAqIGhlcm1lcy11c2FnZSDigJQgdG9rZW4tdXNhZ2UgYmFyIGRvY2tlZCBhdCB0aGUgQk9U"
        "VE9NIG9mIHRoZSBIZXJtZXMgVUkuCiAqCiAqIEJvdHRvbSBwYW5lIChhbHdheXMgdmlzaWJsZSwg"
        "bGlrZSBhIERlZXBTZWVrLUhhcm5lc3MgYm90dG9tIGJhcikgc2hvd2luZyB0aGUKICogRk9DVVNF"
        "RCBzZXNzaW9uJ3MgbGl2ZSB1c2FnZSwgc3RyZWFtZWQgdmlhIGhvc3Quc3RhdGUuZm9jdXNlZFVz"
        "YWdlIChubwogKiBiYWNrZW5kIG5lZWRlZCk6IGlucHV0IC8gb3V0cHV0IC8gY2FjaGUtaGl0JSAv"
        "IHRvdGFsIC8gY2FsbHMgLyBjb3N0LgogKiBDbGljayB0aGUgYmFyIHRvIG9wZW4gdGhlIGZ1bGwg"
        "L3VzYWdlIGRldGFpbCBwYWdlIChyZWFkcyBzdGF0ZS5kYiB2aWEgdGhlCiAqIHNpYmxpbmcgcGx1"
        "Z2luX2FwaS5weSBiYWNrZW5kIGZvciBwZXItbW9kZWwgJiBwZXItc2Vzc2lvbiBoaXN0b3J5KS4K"
        "ICoKICogUGxhaW4gRVNNLCBsb2FkZWQgdW5jb21waWxlZCDigJQgVUkgaXMganN4KCkgY2FsbHMu"
        "IE9ubHkgdGhlc2UgaW1wb3J0cyByZXNvbHZlOgogKiAgIEBoZXJtZXMvcGx1Z2luLXNkaywgcmVh"
        "Y3QsIHJlYWN0L2pzeC1ydW50aW1lCiAqLwoKaW1wb3J0IHsgaG9zdCwgdXNlVmFsdWUsIGhhcHRp"
        "YywgUEFORVNfQVJFQSwgUk9VVEVTX0FSRUEsIFBBTEVUVEVfQVJFQSB9IGZyb20gJ0BoZXJtZXMv"
        "cGx1Z2luLXNkaycKaW1wb3J0IHsganN4LCBqc3hzIH0gZnJvbSAncmVhY3QvanN4LXJ1bnRpbWUn"
        "CmltcG9ydCB7IHVzZUVmZmVjdCwgdXNlU3RhdGUgfSBmcm9tICdyZWFjdCcKCmNvbnN0IElEID0g"
        "J2hlcm1lcy11c2FnZScKY29uc3QgUkVGUkVTSF9NUyA9IDIwMDAwCgovKiAtLS0tLS0tLS0tIG51"
        "bWJlciBmb3JtYXR0aW5nIC0tLS0tLS0tLS0gKi8KZnVuY3Rpb24gZm10KG4pIHsKICBpZiAobiA9"
        "PT0gbnVsbCB8fCBuID09PSB1bmRlZmluZWQgfHwgTnVtYmVyLmlzTmFOKE51bWJlcihuKSkpIHJl"
        "dHVybiAn4oCUJwogIG4gPSBOdW1iZXIobikKICBpZiAobiA8IDApIHJldHVybiAn4oCUJwogIGlm"
        "IChuID49IDFlOSkgcmV0dXJuIChuIC8gMWU5KS50b0ZpeGVkKDIpICsgJ0InCiAgaWYgKG4gPj0g"
        "MWU2KSByZXR1cm4gKG4gLyAxZTYpLnRvRml4ZWQoMikgKyAnTScKICBpZiAobiA+PSAxZTQpIHJl"
        "dHVybiAobiAvIDFlMykudG9GaXhlZCgxKSArICdLJwogIHJldHVybiBNYXRoLnJvdW5kKG4pLnRv"
        "TG9jYWxlU3RyaW5nKCkKfQpmdW5jdGlvbiBmbXRVc2QobikgewogIGlmIChuID09PSBudWxsIHx8"
        "IG4gPT09IHVuZGVmaW5lZCB8fCBuID09PSAwKSByZXR1cm4gJyQwJwogIGlmIChuIDwgMC4wMSkg"
        "cmV0dXJuICckJyArIG4udG9GaXhlZCg0KQogIHJldHVybiAnJCcgKyBuLnRvRml4ZWQoMikKfQpm"
        "dW5jdGlvbiBmbXREYXRlKHNlYykgewogIGlmICghc2VjKSByZXR1cm4gJ+KAlCcKICBjb25zdCBk"
        "ID0gbmV3IERhdGUoc2VjICogMTAwMCkKICBjb25zdCBwID0geCA9PiBTdHJpbmcoeCkucGFkU3Rh"
        "cnQoMiwgJzAnKQogIHJldHVybiBgJHtkLmdldEZ1bGxZZWFyKCl9LSR7cChkLmdldE1vbnRoKCkg"
        "KyAxKX0tJHtwKGQuZ2V0RGF0ZSgpKX0gJHtwKGQuZ2V0SG91cnMoKSl9OiR7cChkLmdldE1pbnV0"
        "ZXMoKSl9YAp9CgovKiAtLS0tLS0tLS0tIGxpdmUgYm90dG9tIGJhciAodGhlIGFsd2F5cy12aXNp"
        "YmxlIG1ldGVyKSAtLS0tLS0tLS0tICovCmZ1bmN0aW9uIE1ldGVyQ2hpcCh7IGxhYmVsLCB2YWx1"
        "ZSwgdGl0bGUgfSkgewogIHJldHVybiBqc3hzKCdzcGFuJywgewogICAgY2xhc3NOYW1lOiAnaW5s"
        "aW5lLWZsZXggaXRlbXMtYmFzZWxpbmUgZ2FwLTEgd2hpdGVzcGFjZS1ub3dyYXAnLAogICAgdGl0"
        "bGU6IHRpdGxlLAogICAgY2hpbGRyZW46IFsKICAgICAganN4KCdzcGFuJywgeyBjbGFzc05hbWU6"
        "ICd0ZXh0LVswLjY4NzVyZW1dIHRleHQtKC0tdWktdGV4dC1xdWF0ZXJuYXJ5KScsIGNoaWxkcmVu"
        "OiBsYWJlbCB9KSwKICAgICAganN4KCdzcGFuJywgeyBjbGFzc05hbWU6ICd0ZXh0LVswLjY4NzVy"
        "ZW1dIGZvbnQtbWVkaXVtIHRhYnVsYXItbnVtcyB0ZXh0LSgtLXVpLXRleHQtc2Vjb25kYXJ5KScs"
        "IGNoaWxkcmVuOiB2YWx1ZSB9KQogICAgXQogIH0pCn0KCmZ1bmN0aW9uIEJvdHRvbUJhcigpIHsK"
        "ICBjb25zdCB1ID0gdXNlVmFsdWUoaG9zdC5zdGF0ZS5mb2N1c2VkVXNhZ2UpCiAgY29uc3Qgb3Bl"
        "biA9ICgpID0+IHsgaGFwdGljKCd0YXAnKTsgaG9zdC5uYXZpZ2F0ZSgnL3VzYWdlJykgfQogIGNv"
        "bnN0IGNoaXAgPSAnaW5saW5lLWZsZXggaC1mdWxsIGl0ZW1zLWNlbnRlciBnYXAtMSBweC0xLjUg"
        "dGV4dC1bMC42ODc1cmVtXSB0cmFuc2l0aW9uLWNvbG9ycyBob3ZlcjpiZy0oLS1jaHJvbWUtYWN0"
        "aW9uLWhvdmVyKSBob3Zlcjp0ZXh0LWZvcmVncm91bmQnCgogIHJldHVybiBqc3goJ2J1dHRvbics"
        "IHsKICAgIHR5cGU6ICdidXR0b24nLAogICAgb25DbGljazogb3BlbiwKICAgIHRpdGxlOiAn54K5"
        "5Ye75omT5byAIFRva2VuIOeUqOmHj+ivpuaDhemhtScsCiAgICBjbGFzc05hbWU6ICdmbGV4IGgt"
        "ZnVsbCB3LWZ1bGwgaXRlbXMtY2VudGVyIGdhcC0zIG92ZXJmbG93LWhpZGRlbiBweC0yIHRleHQt"
        "bGVmdCB0ZXh0LSgtLXVpLXRleHQtc2Vjb25kYXJ5KSBob3Zlcjp0ZXh0LWZvcmVncm91bmQnLAog"
        "ICAgY2hpbGRyZW46ICF1CiAgICAgID8ganN4KCdzcGFuJywgeyBjbGFzc05hbWU6IGNoaXAsIGNo"
        "aWxkcmVuOiAnVG9rZW4g55So6YePIOKAlCDmmoLml6DmtLvliqjkvJror50nIH0pCiAgICAgIDog"
        "anN4cygnc3BhbicsIHsgY2xhc3NOYW1lOiAnZmxleCBpdGVtcy1jZW50ZXIgZ2FwLTMnLAogICAg"
        "ICAgICAgY2hpbGRyZW46IFsKICAgICAgICAgICAganN4KCdzcGFuJywgeyBjbGFzc05hbWU6ICdp"
        "bmxpbmUtZmxleCBpdGVtcy1jZW50ZXIgZ2FwLTEgZm9udC1tZWRpdW0gdGV4dC0oLS11aS1hY2Nl"
        "bnQpJywgY2hpbGRyZW46ICdUb2tlbicgfSksCiAgICAgICAgICAgIGpzeChNZXRlckNoaXAsIHsg"
        "bGFiZWw6ICfovpPlhaUnLCB2YWx1ZTogZm10KHUuaW5wdXQpLCB0aXRsZTogJ+i+k+WFpSB0b2tl"
        "bicgfSksCiAgICAgICAgICAgIGpzeChNZXRlckNoaXAsIHsgbGFiZWw6ICfovpPlh7onLCB2YWx1"
        "ZTogZm10KHUub3V0cHV0KSwgdGl0bGU6ICfovpPlh7ogdG9rZW4nIH0pLAogICAgICAgICAgICB1"
        "LmNhY2hlX2hpdF9wY3QgIT0gbnVsbAogICAgICAgICAgICAgID8ganN4KE1ldGVyQ2hpcCwgeyBs"
        "YWJlbDogJ+e8k+WtmOWRveS4rScsIHZhbHVlOiB1LmNhY2hlX2hpdF9wY3QgKyAnJScsIHRpdGxl"
        "OiAn5b2T5YmN5Lya6K+d5o+Q56S66K+N57yT5a2Y5ZG95Lit546HJyB9KQogICAgICAgICAgICAg"
        "IDoganN4KE1ldGVyQ2hpcCwgeyBsYWJlbDogJ+e8k+WtmCcsIHZhbHVlOiAn4oCUJywgdGl0bGU6"
        "ICdwcm92aWRlciDmnKrkuIrmiqXnvJPlrZgnIH0pLAogICAgICAgICAgICBqc3goTWV0ZXJDaGlw"
        "LCB7IGxhYmVsOiAn5oC7JywgdmFsdWU6IGZtdCh1LnRvdGFsKSwgdGl0bGU6ICfmgLsgdG9rZW7v"
        "vIjlkKvnvJPlrZjvvIknIH0pLAogICAgICAgICAgICBqc3goTWV0ZXJDaGlwLCB7IGxhYmVsOiAn"
        "6LCD55SoJywgdmFsdWU6IHUuY2FsbHMgPz8gMCwgdGl0bGU6ICdBUEkg6LCD55So5qyh5pWwJyB9"
        "KSwKICAgICAgICAgICAgdS5jb3N0X3VzZCAhPSBudWxsID8ganN4KE1ldGVyQ2hpcCwgeyBsYWJl"
        "bDogJ+i0ueeUqCcsIHZhbHVlOiBmbXRVc2QodS5jb3N0X3VzZCksIHRpdGxlOiAn5Lyw566X6LS5"
        "55SoIFVTRCcgfSkgOiBudWxsCiAgICAgICAgICBdCiAgICAgICAgfSkKICB9KQp9CgovKiAtLS0t"
        "LS0tLS0tIGRldGFpbCBwYWdlICgvdXNhZ2UpIOKAlCByZWFkcyBzdGF0ZS5kYiB2aWEgYmFja2Vu"
        "ZCAtLS0tLS0tLS0tICovCmZ1bmN0aW9uIFN0YXRDYXJkKHsgbGFiZWwsIHZhbHVlLCBzdWIsIGFj"
        "Y2VudCB9KSB7CiAgcmV0dXJuIGpzeHMoJ2RpdicsIHsKICAgIGNsYXNzTmFtZTogJ2ZsZXggZmxl"
        "eC1jb2wgZ2FwLTEgcm91bmRlZC1tZCBib3JkZXIgYm9yZGVyLSgtLXVpLXN0cm9rZS1zZWNvbmRh"
        "cnkpIGJnLSgtLXVpLWJnLWVsZXZhdGVkKSBwLTMnLAogICAgY2hpbGRyZW46IFsKICAgICAganN4"
        "KCdkaXYnLCB7IGNsYXNzTmFtZTogJ3RleHQtWzAuNjg3NXJlbV0gdXBwZXJjYXNlIHRyYWNraW5n"
        "LXdpZGUgdGV4dC0oLS11aS10ZXh0LXRlcnRpYXJ5KScsIGNoaWxkcmVuOiBsYWJlbCB9KSwKICAg"
        "ICAganN4KCdkaXYnLCB7CiAgICAgICAgY2xhc3NOYW1lOiBhY2NlbnQgPyAndGV4dC14bCBmb250"
        "LXNlbWlib2xkIHRleHQtKC0tdWktYWNjZW50KScgOiAndGV4dC14bCBmb250LXNlbWlib2xkIHRh"
        "YnVsYXItbnVtcycsCiAgICAgICAgdGl0bGU6IHZhbHVlLAogICAgICAgIGNoaWxkcmVuOiB2YWx1"
        "ZQogICAgICB9KSwKICAgICAgc3ViID8ganN4KCdkaXYnLCB7IGNsYXNzTmFtZTogJ3RleHQtWzAu"
        "Njg3NXJlbV0gdGV4dC0oLS11aS10ZXh0LXRlcnRpYXJ5KScsIGNoaWxkcmVuOiBzdWIgfSkgOiBu"
        "dWxsCiAgICBdCiAgfSkKfQoKZnVuY3Rpb24gVXNhZ2VQYWdlKHsgbG9hZCB9KSB7CiAgY29uc3Qg"
        "W2RhdGEsIHNldERhdGFdID0gdXNlU3RhdGUobnVsbCkKICBjb25zdCBbZXJyb3IsIHNldEVycm9y"
        "XSA9IHVzZVN0YXRlKG51bGwpCiAgY29uc3QgW2xvYWRpbmcsIHNldExvYWRpbmddID0gdXNlU3Rh"
        "dGUodHJ1ZSkKICBjb25zdCBbYXNvZiwgc2V0QXNvZl0gPSB1c2VTdGF0ZShudWxsKQogIGNvbnN0"
        "IFtyZWxvYWRLZXksIHNldFJlbG9hZEtleV0gPSB1c2VTdGF0ZSgwKQoKICB1c2VFZmZlY3QoKCkg"
        "PT4gewogICAgbGV0IGFsaXZlID0gdHJ1ZQogICAgY29uc3QgcnVuID0gKCkgPT4gewogICAgICBs"
        "b2FkKCkudGhlbihyZXMgPT4gewogICAgICAgIGlmICghYWxpdmUpIHJldHVybgogICAgICAgIHNl"
        "dERhdGEocmVzKQogICAgICAgIHNldEVycm9yKHJlcyAmJiByZXMub2sgPT09IGZhbHNlID8gKHJl"
        "cy5lcnJvciB8fCAndXNhZ2UgYmFja2VuZCBlcnJvcicpIDogbnVsbCkKICAgICAgICBzZXRBc29m"
        "KG5ldyBEYXRlKCkpCiAgICAgIH0pLmNhdGNoKGUgPT4gewogICAgICAgIGlmICghYWxpdmUpIHJl"
        "dHVybgogICAgICAgIHNldERhdGEobnVsbCkKICAgICAgICBzZXRFcnJvcigoZSAmJiBlLm1lc3Nh"
        "Z2UpIHx8IFN0cmluZyhlKSkKICAgICAgfSkuZmluYWxseSgoKSA9PiB7IGlmIChhbGl2ZSkgc2V0"
        "TG9hZGluZyhmYWxzZSkgfSkKICAgIH0KICAgIHJ1bigpCiAgICBjb25zdCBpZCA9IHNldEludGVy"
        "dmFsKHJ1biwgUkVGUkVTSF9NUykKICAgIHJldHVybiAoKSA9PiB7IGFsaXZlID0gZmFsc2U7IGNs"
        "ZWFySW50ZXJ2YWwoaWQpIH0KICB9LCBbbG9hZCwgcmVsb2FkS2V5XSkKCiAgaWYgKGxvYWRpbmcg"
        "JiYgIWRhdGEgJiYgIWVycm9yKSB7CiAgICByZXR1cm4ganN4KCdkaXYnLCB7IGNsYXNzTmFtZTog"
        "J2ZsZXggaC1mdWxsIGl0ZW1zLWNlbnRlciBqdXN0aWZ5LWNlbnRlciBwLTggdGV4dC1zbSB0ZXh0"
        "LSgtLXVpLXRleHQtdGVydGlhcnkpJywgY2hpbGRyZW46ICfliqDovb3nlKjph4/mlbDmja7igKYn"
        "IH0pCiAgfQogIGlmIChlcnJvcikgewogICAgcmV0dXJuIGpzeHMoJ2RpdicsIHsKICAgICAgY2xh"
        "c3NOYW1lOiAnZmxleCBoLWZ1bGwgZmxleC1jb2wgaXRlbXMtc3RhcnQganVzdGlmeS1jZW50ZXIg"
        "Z2FwLTMgcC04JywKICAgICAgY2hpbGRyZW46IFsKICAgICAgICBqc3goJ2RpdicsIHsgY2xhc3NO"
        "YW1lOiAndGV4dC1zbSBmb250LW1lZGl1bScsIGNoaWxkcmVuOiAn5peg5rOV6K+75Y+W55So6YeP"
        "5ZCO56uvJyB9KSwKICAgICAgICBqc3goJ3ByZScsIHsgY2xhc3NOYW1lOiAnbWF4LXctZnVsbCB3"
        "aGl0ZXNwYWNlLXByZS13cmFwIHJvdW5kZWQtbWQgYm9yZGVyIGJvcmRlci0oLS11aS1zdHJva2Ut"
        "c2Vjb25kYXJ5KSBiZy0oLS11aS1iZy1lbGV2YXRlZCkgcC0zIHRleHQteHMgdGV4dC0oLS11aS10"
        "ZXh0LXNlY29uZGFyeSknLCBjaGlsZHJlbjogZXJyb3IgfSksCiAgICAgICAganN4KCdkaXYnLCB7"
        "IGNsYXNzTmFtZTogJ3RleHQteHMgdGV4dC0oLS11aS10ZXh0LXRlcnRpYXJ5KScsIGNoaWxkcmVu"
        "OiAn5ZCO56uv6ZyA5Yqg5YWlIHBsdWdpbnMuZW5hYmxlZCDnmb3lkI3ljZXlubblnKggZ2F0ZXdh"
        "eSDph43lkK/lkI7mjILovb3jgILlupXpg6jmnaEo5a6e5pe2KeS4jeS+nei1luWug++8jOacrOmh"
        "tSjljoblj7Ip5L6d6LWW5a6D44CCJyB9KSwKICAgICAgICBqc3goJ2J1dHRvbicsIHsKICAgICAg"
        "ICAgIHR5cGU6ICdidXR0b24nLAogICAgICAgICAgY2xhc3NOYW1lOiAncm91bmRlZC1tZCBiZy0o"
        "LS11aS1hY2NlbnQpIHB4LTMgcHktMS41IHRleHQtc20gaG92ZXI6b3BhY2l0eS05MCcsCiAgICAg"
        "ICAgICBvbkNsaWNrOiAoKSA9PiB7IHNldFJlbG9hZEtleShrID0+IGsgKyAxKTsgc2V0TG9hZGlu"
        "Zyh0cnVlKSB9LAogICAgICAgICAgY2hpbGRyZW46ICfph43or5UnCiAgICAgICAgfSkKICAgICAg"
        "XQogICAgfSkKICB9CgogIGNvbnN0IHQgPSAoZGF0YSAmJiBkYXRhLnRvdGFscykgfHwge30KICBj"
        "b25zdCBtZXRhID0gKGRhdGEgJiYgZGF0YS5tZXRhKSB8fCB7fQogIGNvbnN0IHBlck1vZGVsID0g"
        "KGRhdGEgJiYgZGF0YS5wZXJfbW9kZWwpIHx8IFtdCiAgY29uc3QgcGVyU2Vzc2lvbiA9IChkYXRh"
        "ICYmIGRhdGEucGVyX3Nlc3Npb24pIHx8IFtdCiAgY29uc3QgZGFpbHkgPSAoKGRhdGEgJiYgZGF0"
        "YS5kYWlseSkgfHwgW10pLmZpbHRlcihkID0+IGQuYWN0aXZlKQogIGNvbnN0IGNhY2hlUmF0aW8g"
        "PSB0LmNhY2hlX3NoYXJlX29mX2lucHV0CgogIHJldHVybiBqc3hzKCdkaXYnLCB7CiAgICBjbGFz"
        "c05hbWU6ICdmbGV4IGgtZnVsbCBmbGV4LWNvbCBnYXAtNCBvdmVyZmxvdy15LWF1dG8gcC00JywK"
        "ICAgIGNoaWxkcmVuOiBbCiAgICAgIGpzeHMoJ2RpdicsIHsKICAgICAgICBjbGFzc05hbWU6ICdm"
        "bGV4IGZsZXgtd3JhcCBpdGVtcy1jZW50ZXIgZ2FwLTMnLAogICAgICAgIGNoaWxkcmVuOiBbCiAg"
        "ICAgICAgICBqc3goJ2RpdicsIHsgY2xhc3NOYW1lOiAndGV4dC1iYXNlIGZvbnQtc2VtaWJvbGQn"
        "LCBjaGlsZHJlbjogJ1Rva2VuIOeUqOmHjycgfSksCiAgICAgICAgICBqc3goJ3NwYW4nLCB7IGNs"
        "YXNzTmFtZTogJ3JvdW5kZWQgYmctKC0tdWktYmctZWxldmF0ZWQpIHB4LTEuNSBweS0wLjUgdGV4"
        "dC1bMC42ODc1cmVtXSB0ZXh0LSgtLXVpLXRleHQtc2Vjb25kYXJ5KScsCiAgICAgICAgICAgIGNo"
        "aWxkcmVuOiBgJHttZXRhLm1vZGVscyB8fCAwfSBtb2RlbHMgwrcgJHttZXRhLnNlc3Npb25zIHx8"
        "IDB9IHNlc3Npb25zIMK3ICR7bWV0YS5hcGlfY2FsbHMgfHwgMH0gY2FsbHNgIH0pLAogICAgICAg"
        "ICAganN4KCdzcGFuJywgeyBjbGFzc05hbWU6ICd0ZXh0LVswLjY4NzVyZW1dIHRleHQtKC0tdWkt"
        "dGV4dC10ZXJ0aWFyeSknLAogICAgICAgICAgICBjaGlsZHJlbjogYXNvZiA/ICfmm7TmlrDkuo4g"
        "JyArIGZtdERhdGUoYXNvZi5nZXRUaW1lKCkgLyAxMDAwKSA6ICcnIH0pLAogICAgICAgICAganN4"
        "KCdidXR0b24nLCB7CiAgICAgICAgICAgIHR5cGU6ICdidXR0b24nLAogICAgICAgICAgICBjbGFz"
        "c05hbWU6ICdtbC1hdXRvIHJvdW5kZWQtbWQgYm9yZGVyIGJvcmRlci0oLS11aS1zdHJva2Utc2Vj"
        "b25kYXJ5KSBweC0yIHB5LTEgdGV4dC14cyBob3ZlcjpiZy0oLS1jaHJvbWUtYWN0aW9uLWhvdmVy"
        "KScsCiAgICAgICAgICAgIG9uQ2xpY2s6ICgpID0+IHsgc2V0UmVsb2FkS2V5KGsgPT4gayArIDEp"
        "OyBzZXRMb2FkaW5nKHRydWUpIH0sCiAgICAgICAgICAgIGNoaWxkcmVuOiAn5Yi35pawJwogICAg"
        "ICAgICAgfSkKICAgICAgICBdCiAgICAgIH0pLAogICAgICBqc3hzKCdkaXYnLCB7CiAgICAgICAg"
        "Y2xhc3NOYW1lOiAnZ3JpZCBncmlkLWNvbHMtMiBnYXAtMiBtZDpncmlkLWNvbHMtNCcsCiAgICAg"
        "ICAgY2hpbGRyZW46IFsKICAgICAgICAgIGpzeChTdGF0Q2FyZCwgeyBsYWJlbDogJ+aAuyBUb2tl"
        "bicsIHZhbHVlOiBmbXQodC50b3RhbCksIHN1YjogU3RyaW5nKHQudG90YWwgPz8gJycpLCBhY2Nl"
        "bnQ6IHRydWUgfSksCiAgICAgICAgICBqc3goU3RhdENhcmQsIHsgbGFiZWw6ICfovpPlhaUnLCB2"
        "YWx1ZTogZm10KHQuaW5wdXQpLCBzdWI6IFN0cmluZyh0LmlucHV0ID8/ICcnKSB9KSwKICAgICAg"
        "ICAgIGpzeChTdGF0Q2FyZCwgeyBsYWJlbDogJ+i+k+WHuicsIHZhbHVlOiBmbXQodC5vdXRwdXQp"
        "LCBzdWI6IFN0cmluZyh0Lm91dHB1dCA/PyAnJykgfSksCiAgICAgICAgICBqc3goU3RhdENhcmQs"
        "IHsgbGFiZWw6ICfnvJPlrZjor7vlj5YnLCB2YWx1ZTogZm10KHQuY2FjaGVfcmVhZCksIHN1Yjog"
        "U3RyaW5nKHQuY2FjaGVfcmVhZCA/PyAnJykgfSksCiAgICAgICAgICBqc3goU3RhdENhcmQsIHsg"
        "bGFiZWw6ICfmjqjnkIYnLCB2YWx1ZTogZm10KHQucmVhc29uaW5nKSwgc3ViOiBTdHJpbmcodC5y"
        "ZWFzb25pbmcgPz8gJycpIH0pLAogICAgICAgICAganN4KFN0YXRDYXJkLCB7IGxhYmVsOiAn5Lyw"
        "566X6LS555SoJywgdmFsdWU6IGZtdFVzZCh0LmVzdF91c2QpLCBzdWI6IGAke21ldGEuZXN0X3Jv"
        "d3MgfHwgMH0g6Lev55Sx6K6h5YWl6LS5546HYCwgYWNjZW50OiB0cnVlIH0pLAogICAgICAgICAg"
        "anN4KFN0YXRDYXJkLCB7IGxhYmVsOiAnQVBJIOiwg+eUqCcsIHZhbHVlOiBmbXQodC5hcGlfY2Fs"
        "bHMpLCBzdWI6ICcnIH0pLAogICAgICAgICAganN4KFN0YXRDYXJkLCB7IGxhYmVsOiAn57yT5a2Y"
        "IMO3IOi+k+WFpScsIHZhbHVlOiBjYWNoZVJhdGlvID09IG51bGwgPyAn4oCUJyA6IGNhY2hlUmF0"
        "aW8udG9GaXhlZCgxKSArICd4JywKICAgICAgICAgICAgc3ViOiBjYWNoZVJhdGlvID09IG51bGwg"
        "PyAn5peg5pWw5o2uJyA6ICfor7vlj5bmlL7lpKflgI3mlbDvvIjpnZ7lkb3kuK3njofvvIknIH0p"
        "CiAgICAgICAgXQogICAgICB9KSwKICAgICAganN4cygnZGl2JywgewogICAgICAgIGNsYXNzTmFt"
        "ZTogJ3JvdW5kZWQtbWQgYm9yZGVyIGJvcmRlci0oLS11aS1zdHJva2Utc2Vjb25kYXJ5KSBiZy0o"
        "LS11aS1iZy1lbGV2YXRlZCkgcC0zJywKICAgICAgICBjaGlsZHJlbjogWwogICAgICAgICAganN4"
        "cygnZGl2JywgeyBjbGFzc05hbWU6ICdtYi0yIGZsZXggaXRlbXMtYmFzZWxpbmUgZ2FwLTInLAog"
        "ICAgICAgICAgICBjaGlsZHJlbjogWyBqc3goJ2RpdicsIHsgY2xhc3NOYW1lOiAndGV4dC1zbSBm"
        "b250LW1lZGl1bScsIGNoaWxkcmVuOiAn6L+RIDMwIOWkqei2i+WKvycgfSksCiAgICAgICAgICAg"
        "ICAganN4KCdzcGFuJywgeyBjbGFzc05hbWU6ICd0ZXh0LVswLjY4NzVyZW1dIHRleHQtKC0tdWkt"
        "dGV4dC10ZXJ0aWFyeSknLCBjaGlsZHJlbjogYCR7ZGFpbHkubGVuZ3RofSDkuKrmnInph4/ml6Vg"
        "IH0pIF0gfSksCiAgICAgICAgICBkYWlseS5sZW5ndGggPT09IDAKICAgICAgICAgICAgPyBqc3go"
        "J2RpdicsIHsgY2xhc3NOYW1lOiAncHktNCB0ZXh0LWNlbnRlciB0ZXh0LVswLjgxMjVyZW1dIHRl"
        "eHQtKC0tdWktdGV4dC10ZXJ0aWFyeSknLCBjaGlsZHJlbjogJ+i/kSAzMCDlpKnmsqHmnInnlKjp"
        "h4/orrDlvZUnIH0pCiAgICAgICAgICAgIDoganN4cygnZGl2JywgewogICAgICAgICAgICAgICAg"
        "Y2xhc3NOYW1lOiAnZmxleCBmbGV4LWNvbCBnYXAtMScsCiAgICAgICAgICAgICAgICBjaGlsZHJl"
        "bjogZGFpbHkuc2xpY2UoLTE0KS5tYXAoZCA9PiB7CiAgICAgICAgICAgICAgICAgIGNvbnN0IG14"
        "ID0gTWF0aC5tYXgoLi4uZGFpbHkubWFwKHggPT4geC50b3RhbCB8fCAwKSwgMSkKICAgICAgICAg"
        "ICAgICAgICAgcmV0dXJuIGpzeHMoJ2RpdicsIHsKICAgICAgICAgICAgICAgICAgICBjbGFzc05h"
        "bWU6ICdmbGV4IGl0ZW1zLWNlbnRlciBnYXAtMicsCiAgICAgICAgICAgICAgICAgICAgY2hpbGRy"
        "ZW46IFsKICAgICAgICAgICAgICAgICAgICAgIGpzeCgnc3BhbicsIHsgY2xhc3NOYW1lOiAndy0x"
        "NiBzaHJpbmstMCB0ZXh0LVswLjY4NzVyZW1dIHRhYnVsYXItbnVtcyB0ZXh0LSgtLXVpLXRleHQt"
        "dGVydGlhcnkpJywgY2hpbGRyZW46IGQuZGF0ZS5zbGljZSg1KSB9KSwKICAgICAgICAgICAgICAg"
        "ICAgICAgIGpzeCgnZGl2JywgeyBjbGFzc05hbWU6ICdmbGV4IGZsZXgtMSBnYXAtMC41JywKICAg"
        "ICAgICAgICAgICAgICAgICAgICAgY2hpbGRyZW46IFsKICAgICAgICAgICAgICAgICAgICAgICAg"
        "ICBqc3goJ2RpdicsIHsgY2xhc3NOYW1lOiAnaC0yIHJvdW5kZWQtc20gYmctKC0tdWktYWNjZW50"
        "KSBvcGFjaXR5LTYwJywgc3R5bGU6IHsgd2lkdGg6IE1hdGgubWF4KChkLmNhY2hlX3JlYWQgfHwg"
        "MCkgLyBteCwgMC4wMDQpICogMTAwICsgJyUnIH0gfSksCiAgICAgICAgICAgICAgICAgICAgICAg"
        "ICAganN4KCdkaXYnLCB7IGNsYXNzTmFtZTogJ2gtMiByb3VuZGVkLXNtIGJnLSgtLXVpLWFjY2Vu"
        "dCknLCBzdHlsZTogeyB3aWR0aDogTWF0aC5tYXgoKGQub3V0cHV0IHx8IDApIC8gbXgsIDAuMDA0"
        "KSAqIDEwMCArICclJyB9IH0pCiAgICAgICAgICAgICAgICAgICAgICAgIF0gfSksCiAgICAgICAg"
        "ICAgICAgICAgICAgICBqc3goJ3NwYW4nLCB7IGNsYXNzTmFtZTogJ3ctMTQgc2hyaW5rLTAgdGV4"
        "dC1yaWdodCB0ZXh0LVswLjY4NzVyZW1dIHRhYnVsYXItbnVtcyB0ZXh0LSgtLXVpLXRleHQtc2Vj"
        "b25kYXJ5KScsIHRpdGxlOiAndG90YWwgJyArIChkLnRvdGFsID8/IDApLCBjaGlsZHJlbjogZm10"
        "KGQudG90YWwpIH0pCiAgICAgICAgICAgICAgICAgICAgXQogICAgICAgICAgICAgICAgICB9LCBk"
        "LmRhdGUpCiAgICAgICAgICAgICAgICB9KQogICAgICAgICAgICAgIH0pCiAgICAgICAgXQogICAg"
        "ICB9KSwKICAgICAganN4cygnZGl2JywgewogICAgICAgIGNsYXNzTmFtZTogJ3JvdW5kZWQtbWQg"
        "Ym9yZGVyIGJvcmRlci0oLS11aS1zdHJva2Utc2Vjb25kYXJ5KSBiZy0oLS11aS1iZy1lbGV2YXRl"
        "ZCkgcC0zJywKICAgICAgICBjaGlsZHJlbjogWwogICAgICAgICAganN4KCdkaXYnLCB7IGNsYXNz"
        "TmFtZTogJ21iLTIgdGV4dC1zbSBmb250LW1lZGl1bScsIGNoaWxkcmVuOiAn5oyJ5qih5Z6LJyB9"
        "KSwKICAgICAgICAgIHBlck1vZGVsLmxlbmd0aCA9PT0gMAogICAgICAgICAgICA/IGpzeCgnZGl2"
        "JywgeyBjbGFzc05hbWU6ICdweS0zIHRleHQtY2VudGVyIHRleHQtWzAuODEyNXJlbV0gdGV4dC0o"
        "LS11aS10ZXh0LXRlcnRpYXJ5KScsIGNoaWxkcmVuOiAn5pqC5peg5pWw5o2uJyB9KQogICAgICAg"
        "ICAgICA6IGpzeCgndGFibGUnLCB7CiAgICAgICAgICAgICAgICBjbGFzc05hbWU6ICd3LWZ1bGwg"
        "Ym9yZGVyLWNvbGxhcHNlIHRleHQtWzAuODEyNXJlbV0nLAogICAgICAgICAgICAgICAgY2hpbGRy"
        "ZW46IGpzeHMoJ3Rib2R5JywgewogICAgICAgICAgICAgICAgICBjaGlsZHJlbjogcGVyTW9kZWwu"
        "bWFwKChtLCBpKSA9PiBqc3hzKCd0cicsIHsKICAgICAgICAgICAgICAgICAgICBjbGFzc05hbWU6"
        "ICdib3JkZXItYiBib3JkZXItKC0tdWktc3Ryb2tlLXNlY29uZGFyeSkgbGFzdDpib3JkZXItMCcs"
        "CiAgICAgICAgICAgICAgICAgICAgY2hpbGRyZW46IFsKICAgICAgICAgICAgICAgICAgICAgIGpz"
        "eCgndGQnLCB7IGNsYXNzTmFtZTogJ3B5LTEuNSBwci0yJywgY2hpbGRyZW46IGpzeHMoJ2Rpdics"
        "IHsgY2xhc3NOYW1lOiAnZmxleCBmbGV4LWNvbCcsCiAgICAgICAgICAgICAgICAgICAgICAgIGNo"
        "aWxkcmVuOiBbCiAgICAgICAgICAgICAgICAgICAgICAgICAganN4KCdzcGFuJywgeyBjbGFzc05h"
        "bWU6ICdmb250LW1lZGl1bScsIGNoaWxkcmVuOiBtLm1vZGVsIHx8ICfigJQnIH0pLAogICAgICAg"
        "ICAgICAgICAgICAgICAgICAgIG0ucHJvdmlkZXIgPyBqc3goJ3NwYW4nLCB7IGNsYXNzTmFtZTog"
        "J3RleHQtWzAuNjg3NXJlbV0gdGV4dC0oLS11aS10ZXh0LXRlcnRpYXJ5KScsIGNoaWxkcmVuOiBt"
        "LnByb3ZpZGVyIH0pIDogbnVsbAogICAgICAgICAgICAgICAgICAgICAgICBdIH0pIH0pLAogICAg"
        "ICAgICAgICAgICAgICAgICAgdGMobS5jYWxscywgJ+iwg+eUqCcpLAogICAgICAgICAgICAgICAg"
        "ICAgICAgdGMobS5pbnB1dCwgJ+i+k+WFpScpLAogICAgICAgICAgICAgICAgICAgICAgdGMobS5v"
        "dXRwdXQsICfovpPlh7onKSwKICAgICAgICAgICAgICAgICAgICAgIHRjKG0uY2FjaGVfcmVhZCwg"
        "J+e8k+WtmCcpLAogICAgICAgICAgICAgICAgICAgICAgdGMobS5yZWFzb25pbmcsICfmjqjnkIYn"
        "KSwKICAgICAgICAgICAgICAgICAgICAgIHRjKG0uZXN0X3VzZCA9PSBudWxsID8gbnVsbCA6IGZt"
        "dFVzZChtLmVzdF91c2QpLCAn6LS555SoJykKICAgICAgICAgICAgICAgICAgICBdCiAgICAgICAg"
        "ICAgICAgICAgIH0sIChtLnByb3ZpZGVyIHx8ICcnKSArICfCtycgKyAobS5tb2RlbCB8fCAnJykg"
        "KyAnwrcnICsgaSkpCiAgICAgICAgICAgICAgICB9KQogICAgICAgICAgICAgIH0pCiAgICAgICAg"
        "XQogICAgICB9KSwKICAgICAganN4cygnZGl2JywgewogICAgICAgIGNsYXNzTmFtZTogJ3JvdW5k"
        "ZWQtbWQgYm9yZGVyIGJvcmRlci0oLS11aS1zdHJva2Utc2Vjb25kYXJ5KSBiZy0oLS11aS1iZy1l"
        "bGV2YXRlZCkgcC0zJywKICAgICAgICBjaGlsZHJlbjogWwogICAgICAgICAganN4KCdkaXYnLCB7"
        "IGNsYXNzTmFtZTogJ21iLTIgdGV4dC1zbSBmb250LW1lZGl1bScsIGNoaWxkcmVuOiAn5oyJ5Lya"
        "6K+d77yIVG9wIDMw77yJJyB9KSwKICAgICAgICAgIHBlclNlc3Npb24ubGVuZ3RoID09PSAwCiAg"
        "ICAgICAgICAgID8ganN4KCdkaXYnLCB7IGNsYXNzTmFtZTogJ3B5LTMgdGV4dC1jZW50ZXIgdGV4"
        "dC1bMC44MTI1cmVtXSB0ZXh0LSgtLXVpLXRleHQtdGVydGlhcnkpJywgY2hpbGRyZW46ICfmmoLm"
        "l6DmlbDmja4nIH0pCiAgICAgICAgICAgIDoganN4KCd0YWJsZScsIHsKICAgICAgICAgICAgICAg"
        "IGNsYXNzTmFtZTogJ3ctZnVsbCBib3JkZXItY29sbGFwc2UgdGV4dC1bMC44MTI1cmVtXScsCiAg"
        "ICAgICAgICAgICAgICBjaGlsZHJlbjoganN4cygndGJvZHknLCB7CiAgICAgICAgICAgICAgICAg"
        "IGNoaWxkcmVuOiBwZXJTZXNzaW9uLm1hcCgocywgaSkgPT4ganN4cygndHInLCB7CiAgICAgICAg"
        "ICAgICAgICAgICAgY2xhc3NOYW1lOiAnYm9yZGVyLWIgYm9yZGVyLSgtLXVpLXN0cm9rZS1zZWNv"
        "bmRhcnkpIGxhc3Q6Ym9yZGVyLTAnLAogICAgICAgICAgICAgICAgICAgIGNoaWxkcmVuOiBbCiAg"
        "ICAgICAgICAgICAgICAgICAgICBqc3goJ3RkJywgeyBjbGFzc05hbWU6ICdtYXgtdy1bMjQwcHhd"
        "IHB5LTEuNSBwci0yJywgY2hpbGRyZW46IGpzeHMoJ2RpdicsIHsgY2xhc3NOYW1lOiAnZmxleCBm"
        "bGV4LWNvbCcsCiAgICAgICAgICAgICAgICAgICAgICAgIGNoaWxkcmVuOiBbCiAgICAgICAgICAg"
        "ICAgICAgICAgICAgICAganN4KCdzcGFuJywgeyBjbGFzc05hbWU6ICd0cnVuY2F0ZSBmb250LW1l"
        "ZGl1bScsIHRpdGxlOiBzLnRpdGxlIHx8IHMuc2Vzc2lvbl9pZCwgY2hpbGRyZW46IHMudGl0bGUg"
        "fHwgcy5zZXNzaW9uX2lkIH0pLAogICAgICAgICAgICAgICAgICAgICAgICAgIGpzeCgnc3Bhbics"
        "IHsgY2xhc3NOYW1lOiAndGV4dC1bMC42ODc1cmVtXSB0ZXh0LSgtLXVpLXRleHQtdGVydGlhcnkp"
        "JywKICAgICAgICAgICAgICAgICAgICAgICAgICAgIGNoaWxkcmVuOiAocy5tb2RlbCB8fCAnJykg"
        "KyAocy5wcm92aWRlciA/ICcgwrcgJyArIHMucHJvdmlkZXIgOiAnJykgKyAnIMK3ICcgKyBmbXRE"
        "YXRlKHMubGFzdF9hY3Rpdml0eV9hdCB8fCBzLnN0YXJ0ZWRfYXQpIH0pCiAgICAgICAgICAgICAg"
        "ICAgICAgICAgIF0gfSkgfSksCiAgICAgICAgICAgICAgICAgICAgICB0YyhzLmNhbGxzLCAn6LCD"
        "55SoJyksCiAgICAgICAgICAgICAgICAgICAgICB0YyhzLnRvdGFsLCAn5oC7JyksCiAgICAgICAg"
        "ICAgICAgICAgICAgICB0YyhzLmlucHV0LCAn6L6T5YWlJyksCiAgICAgICAgICAgICAgICAgICAg"
        "ICB0YyhzLm91dHB1dCwgJ+i+k+WHuicpLAogICAgICAgICAgICAgICAgICAgICAgdGMocy5jYWNo"
        "ZV9yZWFkLCAn57yT5a2YJyksCiAgICAgICAgICAgICAgICAgICAgICB0YyhzLmVzdF91c2QgPT0g"
        "bnVsbCA/IG51bGwgOiBmbXRVc2Qocy5lc3RfdXNkKSwgJ+i0ueeUqCcpCiAgICAgICAgICAgICAg"
        "ICAgICAgXQogICAgICAgICAgICAgICAgICB9LCAocy5zZXNzaW9uX2lkIHx8ICdzJykgKyAnwrcn"
        "ICsgaSkpCiAgICAgICAgICAgICAgICB9KQogICAgICAgICAgICAgIH0pCiAgICAgICAgXQogICAg"
        "ICB9KQogICAgXQogIH0pCn0KCmZ1bmN0aW9uIHRjKHYsIGxhYmVsKSB7CiAgcmV0dXJuIGpzeCgn"
        "dGQnLCB7CiAgICBjbGFzc05hbWU6ICdweS0xLjUgcHgtMSB0ZXh0LXJpZ2h0IHRhYnVsYXItbnVt"
        "cyB0ZXh0LSgtLXVpLXRleHQtc2Vjb25kYXJ5KScsCiAgICB0aXRsZTogbGFiZWwsCiAgICBjaGls"
        "ZHJlbjogdiA9PSBudWxsID8gJ+KAlCcgOiB2CiAgfSkKfQoKLyogLS0tLS0tLS0tLSBwbHVnaW4g"
        "ZXhwb3J0IC0tLS0tLS0tLS0gKi8KZXhwb3J0IGRlZmF1bHQgewogIGlkOiBJRCwKICBuYW1lOiAn"
        "VG9rZW4g55So6YePJywKICByZWdpc3RlcihjdHgpIHsKICAgIGNvbnN0IGxvYWQgPSAoKSA9PiBj"
        "dHgucmVzdCgnL292ZXJ2aWV3JykKCiAgICAvLyBBbHdheXMtdmlzaWJsZSBib3R0b20gbWV0ZXIg"
        "KGF1dG8tZG9ja2VkIGJlbG93IHRoZSB3b3Jrc3BhY2UgcGFuZSkuCiAgICBjdHgucmVnaXN0ZXIo"
        "ewogICAgICBpZDogJ3BhbmUnLAogICAgICBhcmVhOiBQQU5FU19BUkVBLAogICAgICB0aXRsZTog"
        "J1Rva2VuIOeUqOmHjycsCiAgICAgIGRhdGE6IHsgcGxhY2VtZW50OiAnYm90dG9tJywgZG9jazog"
        "eyBwYW5lOiAnd29ya3NwYWNlJywgcG9zOiAnYm90dG9tJyB9LCBoZWlnaHQ6ICc0MHB4JyB9LAog"
        "ICAgICByZW5kZXI6ICgpID0+IGpzeChCb3R0b21CYXIsIHt9KQogICAgfSkKCiAgICAvLyBEZXRh"
        "aWwgcGFnZSAoY2xpY2tpbmcgdGhlIGJhciBvcGVucyBpdCkuCiAgICBjdHgucmVnaXN0ZXIoewog"
        "ICAgICBpZDogJ3BhZ2UnLAogICAgICBhcmVhOiBST1VURVNfQVJFQSwKICAgICAgZGF0YTogeyBw"
        "YXRoOiAnL3VzYWdlJyB9LAogICAgICByZW5kZXI6ICgpID0+IGpzeChVc2FnZVBhZ2UsIHsgbG9h"
        "ZCB9KQogICAgfSkKCiAgICBjdHgucmVnaXN0ZXIoewogICAgICBpZDogJ29wZW4nLAogICAgICBh"
        "cmVhOiBQQUxFVFRFX0FSRUEsCiAgICAgIGRhdGE6IHsKICAgICAgICBpZDogJ2hlcm1lcy11c2Fn"
        "ZS5vcGVuJywKICAgICAgICBsYWJlbDogJ+aJk+W8gCBUb2tlbiDnlKjph48nLAogICAgICAgIGtl"
        "eXdvcmRzOiBbJ3VzYWdlJywgJ3Rva2VuJywgJ+eUqOmHjyddLAogICAgICAgIHJ1bjogKCkgPT4g"
        "eyBoYXB0aWMoJ3RhcCcpOyBob3N0Lm5hdmlnYXRlKCcvdXNhZ2UnKSB9CiAgICAgIH0KICAgIH0p"
        "CiAgfQp9Cg=="
    )

B64_plugins_hermes_usage_dashboard_plugin_api_py = (
        "IiIiSGVybWVzIFVzYWdlIOKAlCBwZXJzaXN0ZW50IHRva2VuLXVzYWdlIGJhY2tlbmQgKHJlYWRz"
        "IEhlcm1lcycgb3duIHN0YXRlLmRiKS4KCkEgRmFzdEFQSSByb3V0ZXIgbW91bnRlZCBhdCAvYXBp"
        "L3BsdWdpbnMvaGVybWVzLXVzYWdlLyogYnkgdGhlIGRhc2hib2FyZC9kZXNrdG9wCnBsdWdpbiBz"
        "eXN0ZW0uIEl0IGlzIHRoZSBzZXJ2ZXItc2lkZSBoYWxmIG9mIGEgImRzaC10b2tlbi11c2FnZSIt"
        "c3R5bGUgbG9jYWwKb2JzZXJ2YWJpbGl0eSB0b29sOiBpdCByZWFkcyB0aGUgU0FNRSB1c2FnZSBk"
        "YXRhIEhlcm1lcyBhbHJlYWR5IHBlcnNpc3RzIGluCnN0YXRlLmRiIChzZXNzaW9ucyArIHNlc3Np"
        "b25fbW9kZWxfdXNhZ2UpIGFuZCByZXR1cm5zIGRzaC1zdHlsZSBhZ2dyZWdhdGlvbnMg4oCUCnRv"
        "dGFscywgcGVyIHByb3ZpZGVyL21vZGVsLCBwZXIgc2Vzc2lvbiwgZGFpbHkgdHJlbmQsIGNhY2hl"
        "IHN0cnVjdHVyZSBhbmQKZXN0aW1hdGVkIGNvc3QuIEl0IG5ldmVyIHdyaXRlcyB0byB0aGUgREIg"
        "YW5kIG5ldmVyIHRvdWNoZXMgbW9kZWwgaGlzdG9yeS4KCkVudiBvdmVycmlkZSBmb3IgdGVzdGlu"
        "ZyBvbmx5OiBzZXQgSEVSTUVTX1VTQUdFX0RCIHRvIGEgc3RhdGUuZGIgcGF0aAooZS5nLiBhIGJh"
        "Y2t1cCBzbmFwc2hvdCkgdG8gcG9pbnQgdGhlIHF1ZXJpZXMgYXQgYSBjb3B5LgoiIiIKCmZyb20g"
        "X19mdXR1cmVfXyBpbXBvcnQgYW5ub3RhdGlvbnMKCmltcG9ydCBvcwppbXBvcnQgc3FsaXRlMwpp"
        "bXBvcnQgdGltZQpmcm9tIGRhdGV0aW1lIGltcG9ydCBkYXRldGltZSwgdGltZXpvbmUKZnJvbSBw"
        "YXRobGliIGltcG9ydCBQYXRoCgpmcm9tIGZhc3RhcGkgaW1wb3J0IEFQSVJvdXRlcgoKcm91dGVy"
        "ID0gQVBJUm91dGVyKCkKCiMgTWFwIG9mIFVUQyBkYXRlIHJhbmdlcyBvdmVyIHdoaWNoIGNhY2hl"
        "X3JlYWQvY2FjaGVfd3JpdGUgYXJlIGF1dGhvcml0YXRpdmUuCiMgQ2FjaGUgZmllbGRzIGFyZSBv"
        "bmx5IHN1bW1lZCB3aGVuIHRoZSBzb3VyY2Ugcm93IHBvcHVsYXRlZCB0aGVtIChzZWUgcXVlcmll"
        "cykuCgpfVVRDX0RBWSA9IDg2NDAwLjAKCgpkZWYgX3Jlc29sdmVfZGJfcGF0aCgpIC0+IFBhdGg6"
        "CiAgICBvdmVycmlkZSA9IG9zLmVudmlyb24uZ2V0KCJIRVJNRVNfVVNBR0VfREIiKQogICAgaWYg"
        "b3ZlcnJpZGU6CiAgICAgICAgcmV0dXJuIFBhdGgob3ZlcnJpZGUpCiAgICBob21lID0gb3MuZW52"
        "aXJvbi5nZXQoIkhFUk1FU19IT01FIikKICAgIGlmIG5vdCBob21lOgogICAgICAgIHRyeToKICAg"
        "ICAgICAgICAgZnJvbSBoZXJtZXNfY29uc3RhbnRzIGltcG9ydCBnZXRfcHJvY2Vzc19oZXJtZXNf"
        "aG9tZQoKICAgICAgICAgICAgaG9tZSA9IHN0cihnZXRfcHJvY2Vzc19oZXJtZXNfaG9tZSgpKQog"
        "ICAgICAgIGV4Y2VwdCBFeGNlcHRpb246CiAgICAgICAgICAgIGhvbWUgPSBOb25lCiAgICBpZiBu"
        "b3QgaG9tZToKICAgICAgICBob21lID0gc3RyKFBhdGguaG9tZSgpIC8gIi5oZXJtZXMiKQogICAg"
        "cmV0dXJuIFBhdGgoaG9tZSkgLyAic3RhdGUuZGIiCgoKZGVmIF9jb25uZWN0KGRiX3BhdGg6IFBh"
        "dGgpIC0+IHNxbGl0ZTMuQ29ubmVjdGlvbjoKICAgICIiIlJlYWQtb25seSBjb25uZWN0aW9uOyBk"
        "ZWdyYWRlcyB0byBpbW11dGFibGUgKG5vIFdBTCkgb24gbG9jayBlcnJvcnMuIiIiCiAgICB1cmkg"
        "PSBmImZpbGU6e2RiX3BhdGguYXNfcG9zaXgoKX0/bW9kZT1ybyIKICAgIHRyeToKICAgICAgICBy"
        "ZXR1cm4gc3FsaXRlMy5jb25uZWN0KHVyaSwgdXJpPVRydWUsIHRpbWVvdXQ9NSkKICAgIGV4Y2Vw"
        "dCBzcWxpdGUzLkVycm9yOgogICAgICAgIHBhc3MKICAgIHRyeToKICAgICAgICByZXR1cm4gc3Fs"
        "aXRlMy5jb25uZWN0KHVyaSArICImaW1tdXRhYmxlPTEiLCB1cmk9VHJ1ZSwgdGltZW91dD01KQog"
        "ICAgZXhjZXB0IHNxbGl0ZTMuRXJyb3I6CiAgICAgICAgIyBMYXN0IHJlc29ydDogbm9ybWFsIHJl"
        "YWQtd3JpdGUgb3BlbiAoc2FmZSBmb3IgU0VMRUNUcyBpbiBXQUwgbW9kZSkuCiAgICAgICAgcmV0"
        "dXJuIHNxbGl0ZTMuY29ubmVjdChzdHIoZGJfcGF0aCksIHRpbWVvdXQ9NSkKCgpkZWYgX2Yodik6"
        "CiAgICByZXR1cm4gTm9uZSBpZiB2IGlzIE5vbmUgZWxzZSBmbG9hdCh2KQoKCmRlZiBfbm93X3V0"
        "Y19kYXkoKSAtPiBpbnQ6CiAgICByZXR1cm4gaW50KHRpbWUudGltZSgpKSAvLyA4NjQwMAoKCkBy"
        "b3V0ZXIuZ2V0KCIvaGVhbHRoIikKYXN5bmMgZGVmIGhlYWx0aCgpOgogICAgcmV0dXJuIHsib2si"
        "OiBUcnVlLCAiZGIiOiBzdHIoX3Jlc29sdmVfZGJfcGF0aCgpKX0KCgpAcm91dGVyLmdldCgiL292"
        "ZXJ2aWV3IikKYXN5bmMgZGVmIG92ZXJ2aWV3KCk6CiAgICBkYiA9IF9yZXNvbHZlX2RiX3BhdGgo"
        "KQogICAgaWYgbm90IGRiLmV4aXN0cygpOgogICAgICAgIHJldHVybiB7CiAgICAgICAgICAgICJv"
        "ayI6IEZhbHNlLAogICAgICAgICAgICAiZXJyb3IiOiBmInN0YXRlLmRiIG5vdCBmb3VuZCBhdCB7"
        "ZGJ9IiwKICAgICAgICAgICAgIm1ldGEiOiB7fSwKICAgICAgICAgICAgInRvdGFscyI6IHt9LAog"
        "ICAgICAgICAgICAicGVyX21vZGVsIjogW10sCiAgICAgICAgICAgICJwZXJfc2Vzc2lvbiI6IFtd"
        "LAogICAgICAgICAgICAiZGFpbHkiOiBbXSwKICAgICAgICB9CiAgICBjb25uID0gX2Nvbm5lY3Qo"
        "ZGIpCiAgICBjb25uLnJvd19mYWN0b3J5ID0gc3FsaXRlMy5Sb3cKICAgIHRyeToKICAgICAgICBt"
        "ZXRhID0gZGljdChjb25uLmV4ZWN1dGUoCiAgICAgICAgICAgICJzZWxlY3QgY291bnQoKikgYXMg"
        "YXBpX2NhbGxzLCBjb3VudChkaXN0aW5jdCBzZXNzaW9uX2lkKSBhcyBzZXNzaW9ucywgIgogICAg"
        "ICAgICAgICAiY291bnQoZGlzdGluY3QgbW9kZWwpIGFzIG1vZGVscywgIgogICAgICAgICAgICAi"
        "bWluKGZpcnN0X3NlZW4pIGFzIGZpcnN0X3NlZW4sIG1heChsYXN0X3NlZW4pIGFzIGxhc3Rfc2Vl"
        "biAiCiAgICAgICAgICAgICJmcm9tIHNlc3Npb25fbW9kZWxfdXNhZ2UiCiAgICAgICAgKS5mZXRj"
        "aG9uZSgpKQoKICAgICAgICB0b3RhbHMgPSBkaWN0KGNvbm4uZXhlY3V0ZSgKICAgICAgICAgICAg"
        "InNlbGVjdCBjb2FsZXNjZShzdW0oaW5wdXRfdG9rZW5zKSwwKSBhcyBpbnB1dCwgIgogICAgICAg"
        "ICAgICAiY29hbGVzY2Uoc3VtKG91dHB1dF90b2tlbnMpLDApIGFzIG91dHB1dCwgIgogICAgICAg"
        "ICAgICAiY29hbGVzY2Uoc3VtKGNhY2hlX3JlYWRfdG9rZW5zKSwwKSBhcyBjYWNoZV9yZWFkLCAi"
        "CiAgICAgICAgICAgICJjb2FsZXNjZShzdW0oY2FjaGVfd3JpdGVfdG9rZW5zKSwwKSBhcyBjYWNo"
        "ZV93cml0ZSwgIgogICAgICAgICAgICAiY29hbGVzY2Uoc3VtKHJlYXNvbmluZ190b2tlbnMpLDAp"
        "IGFzIHJlYXNvbmluZywgIgogICAgICAgICAgICAiY29hbGVzY2Uoc3VtKGFwaV9jYWxsX2NvdW50"
        "KSwwKSBhcyBhcGlfY2FsbHMgIgogICAgICAgICAgICAiZnJvbSBzZXNzaW9uX21vZGVsX3VzYWdl"
        "IgogICAgICAgICkuZmV0Y2hvbmUoKSkKCiAgICAgICAgIyBFc3RpbWF0ZWQgY29zdCBhY3Jvc3Mg"
        "dGhlIHdob2xlIHRhYmxlIChlc3RpbWF0ZWQgd2hlcmUgcHJlc2VudCwgZWxzZSBhY3R1YWwpLgog"
        "ICAgICAgIGNvc3QgPSBjb25uLmV4ZWN1dGUoCiAgICAgICAgICAgICJzZWxlY3QgY29hbGVzY2Uo"
        "c3VtKGNvYWxlc2NlKGVzdGltYXRlZF9jb3N0X3VzZCwgYWN0dWFsX2Nvc3RfdXNkLCAwKSksMCkg"
        "YXMgZXN0X3VzZCwgIgogICAgICAgICAgICAiY291bnQoKikgZmlsdGVyICh3aGVyZSBlc3RpbWF0"
        "ZWRfY29zdF91c2QgaXMgbm90IG51bGwgYW5kIGVzdGltYXRlZF9jb3N0X3VzZCA+IDApIGFzIGVz"
        "dF9yb3dzLCAiCiAgICAgICAgICAgICJjb3VudCgqKSBmaWx0ZXIgKHdoZXJlIGFjdHVhbF9jb3N0"
        "X3VzZCBpcyBub3QgbnVsbCBhbmQgYWN0dWFsX2Nvc3RfdXNkID4gMCkgYXMgYWN0X3Jvd3MgIgog"
        "ICAgICAgICAgICAiZnJvbSBzZXNzaW9uX21vZGVsX3VzYWdlIgogICAgICAgICkuZmV0Y2hvbmUo"
        "KQogICAgICAgIG1ldGFbImVzdF9yb3dzIl0gPSBjb3N0WyJlc3Rfcm93cyJdCiAgICAgICAgbWV0"
        "YVsiYWN0X3Jvd3MiXSA9IGNvc3RbImFjdF9yb3dzIl0KICAgICAgICBtZXRhWyJlc3RfdXNkIl0g"
        "PSByb3VuZChfZihjb3N0WyJlc3RfdXNkIl0pIG9yIDAuMCwgNikKCiAgICAgICAgdGluID0gdG90"
        "YWxzWyJpbnB1dCJdIG9yIDAKICAgICAgICBjYWNoZV9yZWFkID0gdG90YWxzWyJjYWNoZV9yZWFk"
        "Il0gb3IgMAogICAgICAgIHRvdGFsc1sidG90YWwiXSA9IHRpbiArICh0b3RhbHNbIm91dHB1dCJd"
        "IG9yIDApICsgY2FjaGVfcmVhZCArICh0b3RhbHNbImNhY2hlX3dyaXRlIl0gb3IgMCkKICAgICAg"
        "ICB0b3RhbHNbImNhY2hlX3NoYXJlX29mX2lucHV0Il0gPSByb3VuZChjYWNoZV9yZWFkIC8gdGlu"
        "LCA0KSBpZiB0aW4gZWxzZSBOb25lCiAgICAgICAgdG90YWxzWyJlc3RfdXNkIl0gPSBtZXRhWyJl"
        "c3RfdXNkIl0KCiAgICAgICAgcGVyX21vZGVsID0gWwogICAgICAgICAgICBkaWN0KHIpCiAgICAg"
        "ICAgICAgIGZvciByIGluIGNvbm4uZXhlY3V0ZSgKICAgICAgICAgICAgICAgICJzZWxlY3QgYmls"
        "bGluZ19wcm92aWRlciBhcyBwcm92aWRlciwgbW9kZWwsIGNvdW50KCopIGFzIGNhbGxzLCAiCiAg"
        "ICAgICAgICAgICAgICAic3VtKGlucHV0X3Rva2VucykgYXMgaW5wdXQsIHN1bShvdXRwdXRfdG9r"
        "ZW5zKSBhcyBvdXRwdXQsICIKICAgICAgICAgICAgICAgICJzdW0oY2FjaGVfcmVhZF90b2tlbnMp"
        "IGFzIGNhY2hlX3JlYWQsIHN1bShjYWNoZV93cml0ZV90b2tlbnMpIGFzIGNhY2hlX3dyaXRlLCAi"
        "CiAgICAgICAgICAgICAgICAic3VtKHJlYXNvbmluZ190b2tlbnMpIGFzIHJlYXNvbmluZywgIgog"
        "ICAgICAgICAgICAgICAgInJvdW5kKHN1bShjb2FsZXNjZShlc3RpbWF0ZWRfY29zdF91c2QsIGFj"
        "dHVhbF9jb3N0X3VzZCwgMCkpLCA2KSBhcyBlc3RfdXNkICIKICAgICAgICAgICAgICAgICJmcm9t"
        "IHNlc3Npb25fbW9kZWxfdXNhZ2UgZ3JvdXAgYnkgYmlsbGluZ19wcm92aWRlciwgbW9kZWwgIgog"
        "ICAgICAgICAgICAgICAgIm9yZGVyIGJ5IChzdW0oaW5wdXRfdG9rZW5zKStzdW0ob3V0cHV0X3Rv"
        "a2Vucykrc3VtKGNhY2hlX3JlYWRfdG9rZW5zKStzdW0oY2FjaGVfd3JpdGVfdG9rZW5zKSkgZGVz"
        "YyIKICAgICAgICAgICAgKS5mZXRjaGFsbCgpCiAgICAgICAgXQogICAgICAgIGZvciByb3cgaW4g"
        "cGVyX21vZGVsOgogICAgICAgICAgICB0ID0gKHJvdy5nZXQoImlucHV0Iikgb3IgMCkgKyAocm93"
        "LmdldCgib3V0cHV0Iikgb3IgMCkKICAgICAgICAgICAgY3IgPSByb3cuZ2V0KCJjYWNoZV9yZWFk"
        "Iikgb3IgMAogICAgICAgICAgICByb3dbInRvdGFsIl0gPSB0ICsgY3IgKyAocm93LmdldCgiY2Fj"
        "aGVfd3JpdGUiKSBvciAwKQogICAgICAgICAgICByb3dbImNhY2hlX3NoYXJlX29mX2lucHV0Il0g"
        "PSByb3VuZChjciAvIChyb3cuZ2V0KCJpbnB1dCIpIG9yIDApLCA0KSBpZiByb3cuZ2V0KCJpbnB1"
        "dCIpIGVsc2UgTm9uZQogICAgICAgICAgICBpZiByb3cuZ2V0KCJlc3RfdXNkIikgaXMgbm90IE5v"
        "bmU6CiAgICAgICAgICAgICAgICByb3dbImVzdF91c2QiXSA9IHJvdW5kKHJvd1siZXN0X3VzZCJd"
        "LCA2KQoKICAgICAgICBwZXJfc2Vzc2lvbiA9IFsKICAgICAgICAgICAgZGljdChyKQogICAgICAg"
        "ICAgICBmb3IgciBpbiBjb25uLmV4ZWN1dGUoCiAgICAgICAgICAgICAgICAic2VsZWN0IHUuc2Vz"
        "c2lvbl9pZCwgY29hbGVzY2Uocy50aXRsZSwgcy5kaXNwbGF5X25hbWUsIHN1YnN0cihzLnNlc3Np"
        "b25fa2V5LDEsNjApLCB1LnNlc3Npb25faWQpIGFzIHRpdGxlLCAiCiAgICAgICAgICAgICAgICAi"
        "cy5zdGFydGVkX2F0LCBzLmxhc3RfYWN0aXZpdHlfYXQsIHUubW9kZWwsIHUuYmlsbGluZ19wcm92"
        "aWRlciBhcyBwcm92aWRlciwgIgogICAgICAgICAgICAgICAgInN1bSh1LmlucHV0X3Rva2Vucykg"
        "YXMgaW5wdXQsIHN1bSh1Lm91dHB1dF90b2tlbnMpIGFzIG91dHB1dCwgIgogICAgICAgICAgICAg"
        "ICAgInN1bSh1LmNhY2hlX3JlYWRfdG9rZW5zKSBhcyBjYWNoZV9yZWFkLCBzdW0odS5jYWNoZV93"
        "cml0ZV90b2tlbnMpIGFzIGNhY2hlX3dyaXRlLCAiCiAgICAgICAgICAgICAgICAic3VtKHUucmVh"
        "c29uaW5nX3Rva2VucykgYXMgcmVhc29uaW5nLCBzdW0odS5hcGlfY2FsbF9jb3VudCkgYXMgY2Fs"
        "bHMsICIKICAgICAgICAgICAgICAgICJyb3VuZChzdW0oY29hbGVzY2UodS5lc3RpbWF0ZWRfY29z"
        "dF91c2QsIHUuYWN0dWFsX2Nvc3RfdXNkLCAwKSksIDYpIGFzIGVzdF91c2QgIgogICAgICAgICAg"
        "ICAgICAgImZyb20gc2Vzc2lvbl9tb2RlbF91c2FnZSB1IGxlZnQgam9pbiBzZXNzaW9ucyBzIG9u"
        "IHMuaWQgPSB1LnNlc3Npb25faWQgIgogICAgICAgICAgICAgICAgImdyb3VwIGJ5IHUuc2Vzc2lv"
        "bl9pZCBvcmRlciBieSAoc3VtKHUuaW5wdXRfdG9rZW5zKStzdW0odS5vdXRwdXRfdG9rZW5zKSsi"
        "CiAgICAgICAgICAgICAgICAic3VtKHUuY2FjaGVfcmVhZF90b2tlbnMpK3N1bSh1LmNhY2hlX3dy"
        "aXRlX3Rva2VucykpIGRlc2MgbGltaXQgMzAiCiAgICAgICAgICAgICkuZmV0Y2hhbGwoKQogICAg"
        "ICAgIF0KICAgICAgICBmb3Igcm93IGluIHBlcl9zZXNzaW9uOgogICAgICAgICAgICB0ID0gKHJv"
        "dy5nZXQoImlucHV0Iikgb3IgMCkgKyAocm93LmdldCgib3V0cHV0Iikgb3IgMCkKICAgICAgICAg"
        "ICAgY3IgPSByb3cuZ2V0KCJjYWNoZV9yZWFkIikgb3IgMAogICAgICAgICAgICByb3dbInRvdGFs"
        "Il0gPSB0ICsgY3IgKyAocm93LmdldCgiY2FjaGVfd3JpdGUiKSBvciAwKQoKICAgICAgICAjIERh"
        "aWx5IHRyZW5kIG92ZXIgdGhlIGxhc3QgTiBjb21wbGV0ZS1pc2ggVVRDIGRheXMsIGJ1Y2tldGVk"
        "IGJ5IGZpcnN0X3NlZW4uCiAgICAgICAgbl9kYXlzID0gMzAKICAgICAgICBzdGFydCA9IF9ub3df"
        "dXRjX2RheSgpIC0gKG5fZGF5cyAtIDEpCiAgICAgICAgcm93cyA9IGNvbm4uZXhlY3V0ZSgKICAg"
        "ICAgICAgICAgInNlbGVjdCBjYXN0KGZpcnN0X3NlZW4gLyA4NjQwMC4wIGFzIGludCkgYXMgZGF5"
        "LCAiCiAgICAgICAgICAgICJzdW0oaW5wdXRfdG9rZW5zKSBhcyBpbnB1dCwgc3VtKG91dHB1dF90"
        "b2tlbnMpIGFzIG91dHB1dCwgIgogICAgICAgICAgICAic3VtKGNhY2hlX3JlYWRfdG9rZW5zKSBh"
        "cyBjYWNoZV9yZWFkLCBzdW0oY2FjaGVfd3JpdGVfdG9rZW5zKSBhcyBjYWNoZV93cml0ZSwgIgog"
        "ICAgICAgICAgICAic3VtKHJlYXNvbmluZ190b2tlbnMpIGFzIHJlYXNvbmluZywgIgogICAgICAg"
        "ICAgICAicm91bmQoc3VtKGNvYWxlc2NlKGVzdGltYXRlZF9jb3N0X3VzZCwgYWN0dWFsX2Nvc3Rf"
        "dXNkLCAwKSksIDYpIGFzIGVzdF91c2QgIgogICAgICAgICAgICAiZnJvbSBzZXNzaW9uX21vZGVs"
        "X3VzYWdlIGdyb3VwIGJ5IGRheSIKICAgICAgICApLmZldGNoYWxsKCkKICAgICAgICBieV9kYXkg"
        "PSB7clsiZGF5Il06IHIgZm9yIHIgaW4gcm93c30KICAgICAgICBkYWlseSA9IFtdCiAgICAgICAg"
        "Zm9yIGQgaW4gcmFuZ2Uoc3RhcnQsIHN0YXJ0ICsgbl9kYXlzKToKICAgICAgICAgICAgciA9IGJ5"
        "X2RheS5nZXQoZCkKICAgICAgICAgICAgZGF5X2RhdGUgPSBkYXRldGltZS5mcm9tdGltZXN0YW1w"
        "KGQgKiBfVVRDX0RBWSwgdHo9dGltZXpvbmUudXRjKS5zdHJmdGltZSgiJVktJW0tJWQiKQogICAg"
        "ICAgICAgICBpZiByIGlzIE5vbmU6CiAgICAgICAgICAgICAgICBkYWlseS5hcHBlbmQoeyJkYXRl"
        "IjogZGF5X2RhdGUsICJkYXkiOiBkLCAiYWN0aXZlIjogRmFsc2V9KQogICAgICAgICAgICAgICAg"
        "Y29udGludWUKICAgICAgICAgICAgdG90YWwgPSAoclsiaW5wdXQiXSBvciAwKSArIChyWyJvdXRw"
        "dXQiXSBvciAwKSArIChyWyJjYWNoZV9yZWFkIl0gb3IgMCkgKyAoclsiY2FjaGVfd3JpdGUiXSBv"
        "ciAwKQogICAgICAgICAgICBkYWlseS5hcHBlbmQoewogICAgICAgICAgICAgICAgImRhdGUiOiBk"
        "YXlfZGF0ZSwgImRheSI6IGQsICJhY3RpdmUiOiBUcnVlLCAidG90YWwiOiB0b3RhbCwKICAgICAg"
        "ICAgICAgICAgICJpbnB1dCI6IHJbImlucHV0Il0gb3IgMCwgIm91dHB1dCI6IHJbIm91dHB1dCJd"
        "IG9yIDAsCiAgICAgICAgICAgICAgICAiY2FjaGVfcmVhZCI6IHJbImNhY2hlX3JlYWQiXSBvciAw"
        "LCAiY2FjaGVfd3JpdGUiOiByWyJjYWNoZV93cml0ZSJdIG9yIDAsCiAgICAgICAgICAgICAgICAi"
        "cmVhc29uaW5nIjogclsicmVhc29uaW5nIl0gb3IgMCwKICAgICAgICAgICAgICAgICJlc3RfdXNk"
        "Ijogcm91bmQoclsiZXN0X3VzZCJdIG9yIDAsIDYpIGlmIHJbImVzdF91c2QiXSBpcyBub3QgTm9u"
        "ZSBlbHNlIE5vbmUsCiAgICAgICAgICAgIH0pCgogICAgICAgIHJldHVybiB7CiAgICAgICAgICAg"
        "ICJvayI6IFRydWUsCiAgICAgICAgICAgICJtZXRhIjogbWV0YSwKICAgICAgICAgICAgInRvdGFs"
        "cyI6IHRvdGFscywKICAgICAgICAgICAgInBlcl9tb2RlbCI6IHBlcl9tb2RlbCwKICAgICAgICAg"
        "ICAgInBlcl9zZXNzaW9uIjogcGVyX3Nlc3Npb24sCiAgICAgICAgICAgICJkYWlseSI6IGRhaWx5"
        "LAogICAgICAgIH0KICAgIGZpbmFsbHk6CiAgICAgICAgY29ubi5jbG9zZSgpCg=="
    )

B64_plugins_hermes_usage_dashboard_manifest_json = (
        "ewogICJuYW1lIjogImhlcm1lcy11c2FnZSIsCiAgImxhYmVsIjogIlRva2VuIOeUqOmHjyIsCiAg"
        "ImRlc2NyaXB0aW9uIjogIlBlcnNpc3RlbnQgdG9rZW4tdXNhZ2UgYmFja2VuZDogcmVhZHMgSGVy"
        "bWVzJyBvd24gc3RhdGUuZGIgKHNlc3Npb25zICsgc2Vzc2lvbl9tb2RlbF91c2FnZSkgYW5kIHNl"
        "cnZlcyBkc2gtdG9rZW4tdXNhZ2Utc3R5bGUgYWdncmVnYXRpb25zIHRvIHRoZSBkZXNrdG9wIC91"
        "c2FnZSBkYXNoYm9hcmQuIEJhY2tlbmQgb25seSDigJQgbm8gd2ViLWRhc2hib2FyZCB0YWIuIiwK"
        "ICAiaWNvbiI6ICJHcmFwaExpbmUiLAogICJ2ZXJzaW9uIjogIjAuMS4wIiwKICAiYXBpIjogInBs"
        "dWdpbl9hcGkucHkiCn0K"
    )

def candidate_homes():
    out = []
    env = os.environ.get("HERMES_HOME")
    if env:
        out.append(Path(env))
    out.append(Path.home() / ".hermes")
    la = os.environ.get("LOCALAPPDATA")
    if la:
        out.append(Path(la) / "hermes")
    dedup = []
    for h in out:
        if h not in dedup:
            dedup.append(h)
    return dedup

def detect(homes):
    env = os.environ.get("HERMES_HOME")
    if env:
        return Path(env)
    scored = []
    for h in homes:
        if not h.exists():
            continue
        s = 0
        if (h / "config.yaml").exists():
            s += 2
        if (h / "state.db").exists():
            s += 4
        if (h / "desktop-plugins").is_dir():
            s += 4
        if (h / "plugins").is_dir():
            s += 2
        if (h / "desktop-plugins" / "hermes-usage").is_dir():
            s += 9
        scored.append((s, h))
    if not scored:
        return (homes[0] if homes else Path.home() / ".hermes")
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]

ARTIFACTS = [
    ("desktop-plugins/hermes-usage/plugin.js", B64_desktop_plugins_hermes_usage_plugin_js),
    ("plugins/hermes-usage/dashboard/plugin_api.py", B64_plugins_hermes_usage_dashboard_plugin_api_py),
    ("plugins/hermes-usage/dashboard/manifest.json", B64_plugins_hermes_usage_dashboard_manifest_json),
]

def write_files(home, bar_only):
    n = 0
    for rel, b64 in ARTIFACTS:
        if bar_only and not rel.startswith("desktop-plugins"):
            continue
        p = home / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(base64.b64decode(b64))
        print("  wrote  %s" % rel)
        n += 1
    return n

def enable_backend(home):
    cfg = home / "config.yaml"
    if not cfg.exists():
        print("  !! 未找到 config.yaml, 跳过后端启用(底部条仍可用; 详情页需要后端)")
        print("     手动启用: hermes config set plugins.enabled \"['hermes-usage']\"")
        return
    try:
        import yaml
    except Exception:
        print("  !! 本机无 PyYAML, 跳过自动启用(不影响底部条)")
        print("     手动启用: hermes config set plugins.enabled \"['hermes-usage']\"")
        return
    try:
        data = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
    except Exception as ex:
        print("  !! 读取 config.yaml 失败 (%s), 跳过自动启用" % ex)
        return
    plugins = data.get("plugins")
    if not isinstance(plugins, dict):
        plugins = {}
        data["plugins"] = plugins
    enabled = plugins.get("enabled")
    if not isinstance(enabled, list):
        enabled = []
    if "hermes-usage" not in enabled:
        enabled.append("hermes-usage")
    plugins["enabled"] = enabled
    bak = cfg.with_name(cfg.name + ".bak-hermes-usage")
    if not bak.exists():
        try:
            bak.write_text(cfg.read_text(encoding="utf-8"), encoding="utf-8")
        except Exception:
            pass
    try:
        cfg.write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
            encoding="utf-8",
        )
        print("  已将 'hermes-usage' 加入 plugins.enabled (原配置已备份为 config.yaml.bak-hermes-usage)")
    except Exception as ex:
        print("  !! 写回 config.yaml 失败 (%s)" % ex)
        print("     手动启用: hermes config set plugins.enabled \"['hermes-usage']\"")

def main():
    bar_only = "--bar-only" in sys.argv
    if "-h" in sys.argv or "--help" in sys.argv:
        print(__doc__)
        return 0
    homes = candidate_homes()
    home = detect(homes)
    print("Hermes 数据目录: %s" % home)
    if not home.exists():
        home.mkdir(parents=True, exist_ok=True)
    n = write_files(home, bar_only)
    print("  写入 %d 个文件" % n)
    if not bar_only:
        enable_backend(home)
    print()
    print("完成。请彻底退出 Hermes 桌面端(含托盘)后重开。")
    print("若底部用量条未出现: Ctrl+K -> Reload desktop plugins")
    return 0

if __name__ == "__main__":
    sys.exit(main())
