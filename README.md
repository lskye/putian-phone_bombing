# 自动化轰炸工具使用说明

## 使用方法
1. 输入要轰炸的手机号
2. 选择Chrome浏览器路径
3. 点击"开始任务"

## 原理
访问api表，打开api表中的链接，给每个莆田系医院发送需求话术+手机号，等待医院给手机号主打电话。

## 名词解释

### 手机号
即你要轰炸的手机号。手机号未做校验，请输入后自行检查（**千万别写自己的！！**）

### 线程数
同时执行任务的数量（api表中一个链接为一条任务）。线程数越大执行越快，资源消耗越多。请根据自己的电脑配置调节到合适的线程数。

### Chrome路径
Chrome浏览器路径，根据系统架构（32位或64位）选择：
- 默认路径为：
  - `C:\Program Files\Google\Chrome\Application\chrome.exe`
  - `C:\Program Files (x86)\Google\Chrome\Application\chrome.exe`

### API表
莆田系医院链接表。

### API表还原
还原初始的API表，主要用于防止误删。

### API表更新
重新从互联网获取可用的莆田系医院链接。

## 文件路径
`C:\Users\【UserName】\AppData\Local\MessageBombingTool`
- `api.txt` - 莆田系医院链接表
- `need_cheat.txt` - 需求话术表

> **注意**：`need_cheat.txt` 为需求话术表，每次会随机选择一条话术+手机号发给医院，可自行修改。
