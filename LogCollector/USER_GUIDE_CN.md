多方法远程日志收集器 - 用户指南（中文）

注意： 本应用程序界面为英文版本。本文档为中文用户指南。

概述

多方法远程日志收集器是一款 Windows Forms 管理工具，用于扫描 Active Directory 域并从多台远程 PC 收集 Agilent/OpenLab 日志文件，采用三层故障转移连接策略。应用程序界面为英文，但本文档提供中文使用说明。

系统要求

- 操作系统： Windows 10/11 或 Windows Server 2016/2019/2022
- 权限： 域管理员账户
- 网络： 可访问 Active Directory 域和目标计算机
- 必需： 必须安装 .NET Framework 4.8 或更高版本（.NET Framework 4.8 已内置在 Windows 10 版本 1809 及更高版本、Windows 11 和 Windows Server 2019/2022 中）
- 注意： PSExec 已随应用程序包含（只需要在收集器机器上，不需要在目标 PC 上）

快速开始

1. 运行应用程序
   - 右键单击 `Remotecollect.exe`
   - 选择"以管理员身份运行"
   - 提示时单击"是"

2. 使用应用程序
   - 单击"扫描域"以发现 PC
   - 选择要收集日志的 PC
   - 单击"收集日志"开始收集
   - 在控制台日志中监控进度

注意： 必须安装 .NET Framework 4.8 或更高版本。.NET Framework 4.8 已内置在 Windows 10 版本 1809 及更高版本、Windows 11 和 Windows Server 2019/2022 中。

开始使用

先决条件

1. 域管理员账户 - 您必须拥有域管理员权限：
   - 如果您以域管理员身份登录，应用程序将直接运行
   - 如果您不是域管理员，应用程序将提示您输入域管理员凭据
   - 所需权限：
     - 域管理员账户
     - Active Directory 读取访问权限
     - 网络管理共享访问权限（C$）
2. .NET Framework 4.8 或更高版本 - 必须在运行此应用程序的 PC 上安装：
   - .NET Framework 4.8 已内置在 Windows 10 版本 1809 及更高版本、Windows 11 和 Windows Server 2019/2022 中
   - 对于较旧的 Windows 版本，必须单独安装 .NET Framework 4.8
   - 下载地址：https://dotnet.microsoft.com/download/dotnet-framework/net48
3. PSExec - 已包含在应用程序文件夹中，用于方法 3 故障转移（只需要在收集器机器上）

运行应用程序

1. 找到可执行文件
   - 应用程序文件名为 `Remotecollect.exe`
   - 它可能与其他必需文件位于同一文件夹中

2. 运行应用程序
   - 右键单击 `Remotecollect.exe`
   - 选择 "以管理员身份运行"
   - 当用户账户控制 (UAC) 提示时，单击 "是"

   如果您不是域管理员：
   - 应用程序将显示凭据对话框
   - 输入您的域管理员凭据：
     - 域： 您的域名（从当前环境预填充）
     - 用户名： 域管理员用户名
     - 密码： 域管理员密码
   - 单击 "确定" 以验证凭据
   - 应用程序将在继续之前验证您的凭据

重要提示： 此应用程序需要域管理员权限。如果无法验证凭据，应用程序将退出。


用户界面概述

注意： 应用程序界面为英文版本。以下为界面元素的中文说明：

应用程序界面包含：

1. 应用程序图标（Application Icon） - 应用程序具有嵌入在可执行文件中的自定义图标，代表远程日志收集工具。图标出现在：
   - Windows 资源管理器（作为 Remotecollect.exe 的文件图标）
   - 应用程序窗口标题栏
   - 应用程序运行时在 Windows 任务栏中
   - 图标嵌入在可执行文件中，因此部署时不需要单独的图标文件
2. "Scan Domain" 按钮（扫描域按钮） - 启动 Active Directory 域扫描（成功扫描后禁用）
3. "Collect Logs" 按钮（收集日志按钮） - 开始从选定的 PC 收集日志
4. 手动 PC 输入（Manual PC Input） - 文本字段和 "Add PC" 按钮，用于通过主机名或 IP 地址手动添加 PC
   - 位于"扫描域"和"收集日志"按钮下方
   - 输入主机名或 IP 地址，然后单击 "Add PC" 将其添加到列表
5. PC 列表（CheckedListBox） - 显示发现的计算机，带复选框供选择（界面显示为英文）
   - 本地主机（主机机器）始终显示在顶部，带有 `[localhost]` 指示器
   - 即使机器不在域中或域扫描失败，本地主机也始终存在
   - 其他计算机按字母顺序列在本地主机下方
6. 进度条（Progress Bar） - 显示多台 PC 的收集进度
7. 状态标签（Status Label） - 显示当前操作状态（英文显示）
8. 控制台日志（RichTextBox） - 带颜色编码消息的实时日志（英文输出）：
   - 青色 - 信息消息（Info）
   - 绿色 - 成功消息（Success）
   - 黄色 - 警告消息（Warning）
   - 红色 - 错误消息（Error）

使用说明

步骤 1：扫描 Active Directory 域或手动添加 PC

首次启动时：
- 本地主机（主机机器）始终显示在 PC 列表顶部，带有 `[localhost]` 指示器
- 如果您之前扫描过域，将自动加载保存的扫描结果
- 状态栏将显示："从保存的扫描结果加载了 X 台计算机（扫描于 YYYY-MM-DD HH:MM:SS）"
- 您可以立即继续，或单击"扫描域"以刷新列表

执行新域扫描：
1. 单击 "Scan Domain"（扫描域） 按钮
2. 应用程序将：
   - 查询 Active Directory 中的所有计算机对象（如果机器在域中）
   - 解析主机名和 IP 地址
   - 在 PC 列表中显示发现的计算机
   - 始终确保本地主机位于顶部，带有 `[localhost]` 指示器
   - 将扫描结果保存到 `DomainScanResults.json`（与可执行文件相同的文件夹）
3. 等待扫描完成（进度条将显示活动）
4. 查看控制台日志以了解扫描结果
5. "扫描域"按钮在成功扫描后将被禁用

注意： 扫描可能需要几分钟，具体取决于域的大小。扫描结果会自动保存，并在下次启动时加载。

注意： 如果您的机器不在域中，域扫描将不会返回额外的计算机，但本地主机仍然可用。您可以使用手动 PC 输入字段手动添加 PC。

手动 PC 输入：
- 在 "Manual PC (hostname or IP):"（手动 PC（主机名或 IP）：）字段中输入主机名或 IP 地址
- 单击 "Add PC"（添加 PC）按钮将其添加到 PC 列表
- 手动添加的 PC 会保存到 `DomainScanResults.json`，并在下次启动时加载
- 您可以一次手动添加多台 PC

保存的扫描结果

应用程序会自动将域扫描结果保存到与可执行文件相同文件夹中的 `DomainScanResults.json`。这允许您：

- 跳过重新扫描： 下次启动时，自动加载保存的结果
- 更快的启动： 无需等待新扫描即可立即开始日志收集
- 离线访问： 即使未连接到域，也可以查看之前扫描的计算机
- 刷新选项： 随时单击"扫描域"以使用当前域状态刷新列表

文件位置： `DomainScanResults.json`（与 `Remotecollect.exe` 相同的文件夹）

注意： 扫描结果包括扫描日期，因此您可以查看列表最后更新的时间。

步骤 2：选择目标 PC

1. 查看 CheckedListBox 中发现的计算机列表（界面显示为英文）
   - 本地主机始终位于顶部，带有 `[localhost]` 指示器
   - 其他计算机（来自域扫描或手动输入）列在下方
2. 勾选要收集日志的 PC 旁边的复选框
   - 您可以选择本地主机、域发现的 PC、手动添加的 PC 或任意组合
3. 可以选择多台 PC 进行批量收集

步骤 3：收集日志

1. 单击 "Collect Logs"（收集日志） 按钮
2. 应用程序将使用三层故障转移策略尝试从每台选定的 PC 收集日志：

方法 1：SMB 管理共享（C$）   - 通过 UNC 路径直接访问文件（\\PCName\C$\...）
   - 可用时最快的方法
   - 需要网络共享访问

方法 2：PowerShell 远程管理（WinRM）   - 使用 Windows 远程管理
   - 在传输前远程压缩日志
   - 需要启用并配置 WinRM

方法 3：PSExec 故障转移   - 使用 Sysinternals PSExec 作为最后手段
   - 执行远程脚本以收集和压缩日志
   - 注意： PSExec 只需要在运行 Remotecollect.exe 的 PC 上（收集器机器），不需要在目标 PC 上

3. 监控进度：
   - 进度条显示完成状态
   - 控制台日志显示每台 PC 的详细信息
   - 状态标签显示当前操作

4. 收集结果保存到：
   ```
   文档\Logs_{会话时间戳}\{主机名}_{时间戳}\
   ```
   - 同一会话中的所有收集都分组在同一个 `Logs_{会话时间戳}` 文件夹中
   - 每台 PC 都有自己的带时间戳的子文件夹
   - 完整的收集过程日志也保存在同一文件夹中

日志收集详情

收集的数据类型

应用程序从每台目标 PC 收集以下类型的信息：

1. Agilent/OpenLab 应用程序日志 - 来自各种 Agilent 软件组件的日志文件
2. 系统信息 - 系统配置、已安装的更新、程序和服务
3. Windows 事件日志 - 应用程序、系统和安全事件日志
4. SQL Server 日志 - SQL Server 错误日志和相关文件（如果安装了 SQL Server）

收集的日志路径

应用程序从以下 Agilent/OpenLab 目录收集日志：

- `C:\Program Files (x86)\Agilent Technologies\OpenLAB Data Store\tomcat\logs` (TomcatLogFiles)
- `C:\ProgramData\Agilent\installLogs` (installLogs)
- `C:\SVReports` (SVReports)
- `C:\ProgramData\Agilent\LogFiles` (CDSLogs)
- `C:\Program Files (x86)\Agilent Technologies\OpenLAB Services\Licensing\Flexera\logs` (flexLogs)
- `C:\Program Files (x86)\Agilent Technologies\Content Management Search Services\logs` (searchLogs)
- `C:\Program Files (x86)\Agilent Technologies\Content Management Search Services\solr\server\logs` (SolrLogs)
- `C:\Program Files (x86)\Agilent Technologies\OpenLab Reverse Proxy Configuration Service\ConfigurationService\logs\service` (RPCFGlogs)
- `C:\Program Files\OpenLab Reverse Proxy\Apache24\logs` (2.7RPlogs)
- `C:\Program Files (x86)\OpenLab Reverse Proxy\Apache24\logs` (2.6RPlogs)
- `C:\ProgramData\Agilent\installation` (installConf)
- `C:\ProgramData\Agilent\OpenLab ECM XT Import Scheduler\Logs` (imporschedulerlog)
- `D:\MassHunter\log` (MassHunterLog)
- `C:\ProgramData\Agilent Technologies\ChemStation` (ChemstationLog)

收集的系统信息

对于每台 PC，收集以下系统信息：

- 系统配置 (`systeminfo.txt`) - 完整的系统信息，包括操作系统版本、硬件详情、网络配置
- 已安装的更新 (`installed_updates.txt`) - Windows 补丁和更新列表，按安装日期排序
- 已安装的程序 (`installed_programs.txt`) - Windows 注册表中的所有已安装软件列表
- 系统服务 (`system_services.txt`) - 所有 Windows 服务的状态和详情

收集的 Windows 事件日志

以下 Windows 事件日志导出为 `.evtx` 文件：

- Application.evtx - 应用程序级别的事件和错误
- System.evtx - 系统级别的事件、驱动程序问题和硬件问题
- Security.evtx - 安全相关事件，包括登录尝试和访问控制

SQL Server 日志

如果目标 PC 上安装了 SQL Server，应用程序将自动检测并收集：

- SQL Server 错误日志（ERRORLOG 文件）
- 找到的所有 SQL Server 实例的日志文件
- 位于标准 SQL Server 安装目录中

文件过滤

- 排除： 所有 `.dmp`（内存转储）文件自动排除在收集之外
- 包含： 目标目录中的所有其他日志文件

输出结构

收集的日志按以下方式组织：

```
文档\Logs_{会话时间戳}\
  ├── PC-NAME_20241215_143022\
  ├── CollectionProcessLog_{时间戳}.txt\
      ├── System_Info\
      │   ├── systeminfo.txt
      │   ├── installed_updates.txt
      │   ├── installed_programs.txt
      │   ├── system_services.txt
      │   └── EventLogs\
      │       ├── Application.evtx
      │       ├── System.evtx
      │       └── Security.evtx
      ├── SQLServer_Logs\
      │   └── [SQL 实例文件夹，包含错误日志]
      ├── TomcatLogFiles\
      ├── installLogs\
      ├── SVReports\
      ├── CDSLogs\
      ├── flexLogs\
      ├── searchLogs\
      ├── SolrLogs\
      ├── RPCFGlogs\
      ├── 2.7RPlogs\
      ├── 2.6RPlogs\
      ├── installConf\
      ├── imporschedulerlog\
      ├── MassHunterLog\
      └── ChemstationLog\
```

故障排除

域扫描问题

问题： 未找到计算机
- 解决方案： 验证您拥有域管理员权限并可以访问 Active Directory

问题： 扫描失败，显示访问被拒绝
- 解决方案： 确保以域管理员身份运行并拥有适当的 AD 权限

连接方法失败

方法 1（SMB）失败：- 验证与目标 PC 的网络连接
- 检查是否启用了管理共享（C$）
- 确保防火墙允许 SMB 流量（端口 445）

方法 2（WinRM）失败：- 验证目标 PC 上是否启用了 WinRM：
  ```powershell
  Enable-PSRemoting -Force
  ```
- 检查 WinRM 服务是否正在运行
- 验证防火墙是否允许 WinRM（端口 5985/5986）

方法 3（PSExec）失败：- 确保 PSExec.exe 与 Remotecollect.exe 位于同一文件夹中（或在收集器机器的系统 PATH 中）
- 注意： PSExec 只需要在收集器机器上，不需要在目标 PC 上
- 验证目标 PC 允许远程执行
- 检查防火墙是否允许 RPC/DCOM 流量

一般问题

应用程序无法启动：- 确保以管理员身份运行 `Remotecollect.exe`（右键单击 → "Run as administrator" / 以管理员身份运行）
- 检查是否安装了 .NET Framework 4.8： 检查 Windows 功能或控制面板 > 程序和功能
  - .NET Framework 4.8 已内置在 Windows 10 版本 1809 及更高版本、Windows 11 和 Windows Server 2019/2022 中
  - 对于较旧的 Windows 版本，请从以下地址下载并安装：https://dotnet.microsoft.com/download/dotnet-framework/net48
- 检查可执行文件是否被阻止（右键单击 → 属性 → 如果存在则取消阻止）
- 验证所有必需文件是否与可执行文件位于同一文件夹中（包括 PSExec.exe，如果存在）
- 确保 Windows Defender 或防病毒软件未阻止应用程序
- 查看 Windows 事件查看器中的错误

收集时间过长：- 大型日志目录可能需要时间
- 网络延迟影响传输速度
- 考虑一次从较少的 PC 收集

未收集到日志：- 验证目标 PC 上是否安装了 Agilent/OpenLab
- 检查日志目录是否存在
- 查看控制台日志中的具体错误消息

未收集系统信息：- 验证 PowerShell 远程管理是否可用（对于 WinRM 方法）
- 检查目标 PC 是否允许远程命令执行
- 确保管理共享可访问（对于 SMB 方法）

未收集事件日志：- 验证您是否有权限读取目标 PC 上的事件日志
- 检查目标 PC 上的事件日志服务是否正在运行
- 某些事件日志（特别是安全日志）可能需要额外权限

未找到 SQL Server 日志：- 仅当安装了 SQL Server 时才会收集 SQL Server 日志
- 验证 SQL Server 安装路径是否为标准路径
- 查看控制台日志中的 SQL Server 检测消息

最佳实践

1. 在非工作时间运行 - 日志收集可能占用大量资源
2. 策略性选择 PC - 从几台 PC 开始测试连接性
3. 监控控制台日志 - 注意警告和错误
4. 验证输出 - 完成后检查收集的日志文件夹
5. 保持 PSExec 更新 - 如果使用方法 3，请确保在收集器机器上使用最新版本（目标 PC 不需要 PSExec）

安全注意事项

- 此工具需要域管理员权限
- 收集的日志可能包含敏感信息
- 安全存储收集的日志
- 遵循组织的数据保留政策
- 在共享或归档前审查日志

支持

注意： 应用程序界面和日志消息均为英文。如有问题或疑问：
1. 查看控制台日志中的详细错误消息（英文显示）
2. 验证是否满足所有先决条件
3. 查看上述故障排除部分
4. 如果问题持续存在，请联系 IT 管理员

语言说明

- 应用程序界面： 英文
- 控制台日志： 英文
- 错误消息： 英文
- 本文档： 中文（提供使用说明和界面元素翻译）

版本信息

- 版本： 1.0.2.1
- 发布： 260212
- 可执行文件： Remotecollect.exe
- 目标框架： .NET Framework 4.8
- 平台： Windows Forms
- 分发方式： 框架依赖可执行文件（需要安装 .NET Framework 4.8 或更高版本）
- 包含的工具： PSExec（用于方法 3 故障转移）
- 应用程序图标： 嵌入在可执行文件中的自定义多分辨率图标（log8.ico）。图标作为资源嵌入，因此部署时不需要单独的图标文件。图标会出现在 Windows 资源管理器、应用程序窗口和任务栏中。

版本 260212 功能

- 手动 PC 输入： 添加了手动 PC 输入字段和 "Add PC" 按钮，允许通过主机名或 IP 地址添加 PC，无需域扫描
- 本地主机始终存在： 本地主机始终显示在 PC 列表顶部，带有 `[localhost]` 指示器，无论域成员身份或扫描结果如何
- 非域支持： 即使机器不在域中，应用程序也能正常工作 - 域扫描会优雅地返回空列表，但本地主机和手动添加的 PC 仍然可用
- UI 布局改进： 重新组织了 UI 布局，将"扫描域"和"收集日志"按钮放在顶部，手动 PC 输入在下方，PC 列表在更下方
- 增强的灵活性： 用户现在可以从本地主机和手动指定的 PC 收集日志，无需 Active Directory 域成员身份

版本 20260212 功能

- .NET Framework 4.8 兼容性： 应用程序现在面向 .NET Framework 4.8，以提高兼容性和稳定性
- 改进的兼容性： 所有组件已更新以兼容 .NET Framework 4.8
- 增强的稳定性： 修复了 JSON 序列化和可空类型的兼容性问题

版本 260211 功能

- 凭据对话框： 如果当前用户不是域管理员，应用程序会提示输入域管理员凭据，并清楚说明所需权限
- 扫描结果持久化： 域扫描结果自动保存到 `DomainScanResults.json`，并在启动时加载，无需每次都重新扫描
- 改进的用户体验：
  - 通过自动加载保存的扫描结果实现更快的启动
  - 状态栏中显示扫描日期
  - 随时可以使用"扫描域"按钮刷新扫描结果

先前版本功能（20260208）

- 本地主机检测： 域扫描后自动将主机机器添加到 PC 列表，带有 `[localhost]` 指示器
- 时间戳组织： 同一会话中的所有收集都分组在 `Logs_{会话时间戳}` 文件夹中，以便更好地组织
- 控制台日志保存： 完整的收集过程日志自动保存到同一文件夹中的 `CollectionProcessLog_{时间戳}.txt`
- UI 改进：
  - 成功扫描后禁用"扫描域"按钮，以防止不必要的重新扫描
  - 改进了窗口调整大小和全屏模式的布局处理

---

最后更新： 2026年2月
