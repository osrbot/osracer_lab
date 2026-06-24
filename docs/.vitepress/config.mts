import { defineConfig } from "vitepress";

const zhNav = [
  { text: "新手入门", link: "/getting-started" },
  { text: "仿真训练", link: "/training" },
  { text: "实车部署", link: "/sim2real" },
  { text: "参数接口", link: "/hardware_parameters" }
];

const enNav = [
  { text: "Getting Started", link: "/en/getting-started" },
  { text: "Training", link: "/en/training" },
  { text: "Real Car", link: "/en/sim2real" },
  { text: "Parameters", link: "/en/hardware_parameters" }
];

const zhSidebar = [
  {
    text: "新手入门",
    items: [
      { text: "首页", link: "/" },
      { text: "快速开始", link: "/getting-started" },
      { text: "安装环境", link: "/installation" },
      { text: "常见问题", link: "/troubleshooting" }
    ]
  },
  {
    text: "仿真训练",
    items: [
      { text: "训练与导出", link: "/training" },
      { text: "Sim2Sim", link: "/sim2sim" },
      { text: "MuJoCo 验证", link: "/mujoco_sim2sim" }
    ]
  },
  {
    text: "实车部署",
    items: [
      { text: "Sim2Real / Jetson", link: "/sim2real" },
      { text: "实车参数", link: "/real-car" },
      { text: "标定流程", link: "/calibration" },
      { text: "外参对齐", link: "/extrinsics_alignment" }
    ]
  },
  {
    text: "参数与接口",
    items: [
      { text: "硬件参数", link: "/hardware_parameters" },
      { text: "运行时接口约定", link: "/deployment" },
      { text: "feat-demo 参数核对", link: "/feat_demo_parameter_audit" },
      { text: "实车测量清单", link: "/real_car_measurement_checklist" },
      { text: "参数填写表", link: "/real_car_parameter_fill_sheet" }
    ]
  },
  {
    text: "项目状态",
    items: [
      { text: "当前状态", link: "/current_implementation_status" },
      { text: "推送准备", link: "/handoff_push_readiness" }
    ]
  }
];

const enSidebar = [
  {
    text: "Getting Started",
    items: [
      { text: "Home", link: "/en/" },
      { text: "Quick Start", link: "/en/getting-started" },
      { text: "Installation", link: "/en/installation" },
      { text: "Troubleshooting", link: "/en/troubleshooting" }
    ]
  },
  {
    text: "Simulation Training",
    items: [
      { text: "Training and Export", link: "/en/training" },
      { text: "Sim2Sim", link: "/en/sim2sim" },
      { text: "MuJoCo Validation", link: "/en/mujoco_sim2sim" }
    ]
  },
  {
    text: "Real-Car Deployment",
    items: [
      { text: "Sim2Real / Jetson", link: "/en/sim2real" },
      { text: "Real-Car Parameters", link: "/en/real-car" },
      { text: "Calibration", link: "/en/calibration" },
      { text: "Extrinsics Alignment", link: "/en/extrinsics_alignment" }
    ]
  },
  {
    text: "Parameters and Interfaces",
    items: [
      { text: "Hardware Parameters", link: "/en/hardware_parameters" },
      { text: "Runtime Interface", link: "/en/deployment" },
      { text: "feat-demo Parameter Audit", link: "/en/feat_demo_parameter_audit" },
      { text: "Measurement Checklist", link: "/en/real_car_measurement_checklist" },
      { text: "Parameter Fill Sheet", link: "/en/real_car_parameter_fill_sheet" }
    ]
  },
  {
    text: "Project Status",
    items: [
      { text: "Current Status", link: "/en/current_implementation_status" },
      { text: "Push Readiness", link: "/en/handoff_push_readiness" }
    ]
  }
];

const commonTheme = {
  logo: "/osracer-mark.svg",
  siteTitle: "OSRacer Isaac Lab",
  socialLinks: [
    { icon: "github", link: "https://github.com/osrbot/osracer_lab" }
  ],
  search: {
    provider: "local" as const,
    options: {
      locales: {
        root: {
          translations: {
            button: { buttonText: "搜索", buttonAriaLabel: "搜索" },
            modal: {
              displayDetails: "显示详情",
              resetButtonTitle: "清除搜索",
              backButtonTitle: "关闭搜索",
              noResultsText: "没有找到结果",
              footer: {
                selectText: "选择",
                navigateText: "切换",
                closeText: "关闭"
              }
            }
          }
        }
      }
    }
  }
};

export default defineConfig({
  title: "OSRacer Isaac Lab",
  description: "OSRacer Isaac Lab training, sim2sim, sim2real, and Jetson deployment guide.",
  base: "/osracer_lab/",
  cleanUrls: true,
  lastUpdated: true,
  ignoreDeadLinks: [/^https?:\/\//],
  themeConfig: {
    ...commonTheme,
    nav: zhNav,
    sidebar: zhSidebar,
    outline: {
      level: [2, 3],
      label: "本页目录"
    },
    docFooter: {
      prev: "上一页",
      next: "下一页"
    },
    lastUpdated: {
      text: "最后更新",
      formatOptions: {
        dateStyle: "medium",
        timeStyle: "short"
      }
    },
    langMenuLabel: "语言",
    returnToTopLabel: "回到顶部",
    sidebarMenuLabel: "菜单",
    darkModeSwitchLabel: "深色模式",
    lightModeSwitchTitle: "切换到浅色模式",
    darkModeSwitchTitle: "切换到深色模式"
  },
  locales: {
    root: {
      label: "简体中文",
      lang: "zh-CN",
      title: "OSRacer Isaac Lab",
      description: "OSRacer Isaac Lab 仿真训练、sim2sim、sim2real 与 Jetson 部署指南。"
    },
    en: {
      label: "English",
      lang: "en-US",
      title: "OSRacer Isaac Lab",
      description: "OSRacer Isaac Lab training, sim2sim, sim2real, and Jetson deployment guide.",
      themeConfig: {
        ...commonTheme,
        nav: enNav,
        sidebar: enSidebar,
        outline: {
          level: [2, 3],
          label: "On this page"
        },
        docFooter: {
          prev: "Previous",
          next: "Next"
        },
        lastUpdated: {
          text: "Last updated",
          formatOptions: {
            dateStyle: "medium",
            timeStyle: "short"
          }
        },
        langMenuLabel: "Language",
        returnToTopLabel: "Return to top",
        sidebarMenuLabel: "Menu",
        darkModeSwitchLabel: "Appearance",
        lightModeSwitchTitle: "Switch to light theme",
        darkModeSwitchTitle: "Switch to dark theme"
      }
    }
  },
  markdown: {
    lineNumbers: false
  }
});
