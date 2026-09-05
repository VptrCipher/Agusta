import type {ThemeConfig} from 'antd'
import {theme} from 'antd'
import {elevation, paper, palette, radius} from './palette'
import {fontFamilyMono, fontFamilySans} from './utils/typography'

const themeConfig: ThemeConfig = {
  algorithm: theme.darkAlgorithm,
  token: {
    colorPrimary: palette.primary,
    colorInfo: palette.primary,
    colorSuccess: palette.success,
    colorWarning: palette.warning,
    colorError: palette.error,

    colorBgBase: palette.bgBase,
    colorBgLayout: palette.bgBase,
    colorBgContainer: palette.bgContainer,
    colorBgElevated: palette.bgElevated,
    colorBgSpotlight: palette.bgElevated,
    colorBgMask: palette.bgMask,

    colorBorder: palette.border,
    colorBorderSecondary: palette.borderSoft,

    colorText: palette.text,
    colorTextSecondary: palette.textSecondary,
    colorTextTertiary: palette.textTertiary,
    colorTextQuaternary: palette.textQuaternary,

    colorLink: palette.primary,
    colorLinkHover: palette.primaryHover,
    colorLinkActive: palette.primaryActive,

    fontFamily: fontFamilySans,
    fontFamilyCode: fontFamilyMono,
    fontSize: 14,
    lineHeight: 1.5715,

    borderRadius: radius.md,
    borderRadiusSM: radius.sm,
    borderRadiusLG: radius.lg,
    borderRadiusXS: 4,

    controlHeight: 34,
    wireframe: false,

    boxShadow: elevation.card,
    boxShadowSecondary: elevation.raised,
    boxShadowTertiary: elevation.card,
  },
  components: {
    Layout: {
      headerBg: palette.bgContainer,
      bodyBg: palette.bgBase,
      siderBg: palette.bgLayout,
      headerHeight: 48,
      headerPadding: '0 16px',
    },
    Menu: {
      itemBg: 'transparent',
      subMenuItemBg: 'transparent',
      itemColor: palette.textSecondary,
      itemHoverColor: palette.text,
      itemHoverBg: paper(0.05),
      itemSelectedColor: palette.primary,
      itemSelectedBg: palette.primaryBg,
      itemMarginInline: 8,
      itemBorderRadius: radius.md,
      activeBarWidth: 0,
    },
    Card: {
      colorBgContainer: palette.bgContainer,
      headerBg: 'transparent',
      borderRadiusLG: radius.lg,
      boxShadowTertiary: elevation.card,
    },
    Table: {
      headerBg: palette.bgLayout,
      headerColor: palette.textSecondary,
      headerSplitColor: 'transparent',
      rowHoverBg: paper(0.045),
      rowSelectedBg: palette.primaryBg,
      rowSelectedHoverBg: palette.primaryBgHover,
      borderColor: palette.borderSoft,
      cellPaddingBlock: 10,
    },
    Button: {
      primaryShadow: 'none',
      defaultShadow: 'none',
      dangerShadow: 'none',
      fontWeight: 500,
    },
    Input: {
      activeBorderColor: palette.primary,
      hoverBorderColor: palette.primaryBorder,
      activeShadow: elevation.focus,
      colorBgContainer: palette.bgWell,
    },
    InputNumber: {
      activeBorderColor: palette.primary,
      hoverBorderColor: palette.primaryBorder,
      activeShadow: elevation.focus,
      colorBgContainer: palette.bgWell,
    },
    Select: {
      optionSelectedBg: palette.primaryBg,
      optionSelectedColor: palette.text,
      colorBgContainer: palette.bgWell,
    },
    Segmented: {
      itemColor: palette.textSecondary,
      itemHoverColor: palette.text,
      itemSelectedBg: palette.primaryBg,
      itemSelectedColor: palette.primary,
      trackBg: paper(0.04),
      trackPadding: 3,
      borderRadius: radius.md,
    },
    Tabs: {
      itemColor: palette.textSecondary,
      itemHoverColor: palette.text,
      itemSelectedColor: palette.primary,
      inkBarColor: palette.primary,
      titleFontSize: 14,
    },
    Modal: {
      contentBg: palette.bgContainer,
      headerBg: palette.bgContainer,
      footerBg: 'transparent',
      borderRadiusLG: radius.lg,
      boxShadow: elevation.overlay,
    },
    Drawer: {
      colorBgElevated: palette.bgContainer,
    },
    Tooltip: {
      colorBgSpotlight: palette.bgElevated,
      colorTextLightSolid: palette.text,
    },
    Tag: {
      defaultBg: paper(0.05),
      defaultColor: palette.textSecondary,
      borderRadiusSM: radius.sm,
    },
    Progress: {
      defaultColor: palette.primary,
      remainingColor: paper(0.08),
    },
    Divider: {
      colorSplit: palette.borderSoft,
    },
    Breadcrumb: {
      itemColor: palette.textTertiary,
      lastItemColor: palette.text,
      linkColor: palette.textTertiary,
      linkHoverColor: palette.primary,
      separatorColor: palette.textQuaternary,
    },
    Statistic: {
      contentFontSize: 26,
      titleFontSize: 12,
    },
    Badge: {
      colorBgContainer: palette.bgContainer,
    },
    Alert: {
      borderRadiusLG: radius.md,
    },
    Avatar: {
      colorTextPlaceholder: palette.primaryActive,
    },
    Empty: {
      colorTextDescription: palette.textTertiary,
    },
  },
}

export {palette, severityColors, severityTagColors} from './palette'

export default themeConfig
