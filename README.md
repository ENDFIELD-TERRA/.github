# 组织主页

[查看 ENDFIELD-TERRA](https://github.com/ENDFIELD-TERRA)

公开主页由 [profile/README.md](profile/README.md) 提供，图形位于 `assets/`。

- [参与指南](CONTRIBUTING.md)
- [字体、引文与素材署名](ATTRIBUTION.md)
- [视觉约定](DESIGN.md)

主视觉使用 SVG 轮廓、动画 WebP 与 GIF 兼容图，查看者无需安装字体。`tools/render_hero.py` 可用 `requirements-render.txt` 中的依赖重新生成主视觉；它不属于访客端运行依赖。

## Public 与 Member 视图

公共视图读取本仓库的 `profile/README.md`；成员视图读取私有仓库 `ENDFIELD-TERRA/.github-private` 中同路径的镜像。两版共用本仓库的公开图片地址。

发布公共 README 的文字或结构更新后，运行 `python tools/sync_member_profile.py` 同步成员版；`python tools/sync_member_profile.py --check` 只核对一致性。脚本使用现有 gh 登录，不保存令牌，也不设置定时任务。
