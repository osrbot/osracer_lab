import { defineConfig } from "vitepress";

export default defineConfig({
  title: "OSRacer Isaac Lab",
  description: "OSRacer Isaac Lab training, sim2sim, sim2real, and Jetson deployment guide.",
  base: "/osracer_lab/",
  cleanUrls: true,
  lastUpdated: true,
  ignoreDeadLinks: [/^https?:\/\//],
  themeConfig: {
    logo: "/osracer-mark.svg",
    siteTitle: "OSRacer Isaac Lab",
    nav: [
      { text: "新手入门", link: "/getting-started" },
      { text: "仿真训练", link: "/training" },
      { text: "实车部署", link: "/sim2real" },
      { text: "参数接口", link: "/hardware_parameters" }
    ],
    sidebar: [
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
    ],
    socialLinks: [
      { icon: "github", link: "https://github.com/osrbot/osracer_lab" }
    ],
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
    search: {
      provider: "local"
    }
  },
  markdown: {
    lineNumbers: false
  }
});
