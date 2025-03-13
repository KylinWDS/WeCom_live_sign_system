企微直播邀请签到系统
我现在有一个要做客户端的需求，最终交付客户需要一个exe可执行文件，相关需求描述如下：
1.开发语言请使用Python3，数据库存储数据请使用SQLite
2.图形化界面等等相关内容需要使用开源免费可商用的依赖
3.需求内容是相关与企业微信直播相关的数据统计
4.对于客户端开始框架逐层描述，首页如下：
4.1.开屏做首页，首页要做到页面精美，符合现在流行审美，页面需要附带整体颜色风格调整，分为3种：跟随系统颜色、明亮、暗色
4.2.首页需要有6个输入框，分别为：企业名称(corpname)(不许重复)、企业ID(corpid)、企业应用Secret(corpsecret)、应用ID(AgentId)、用户ID(userid)(用户ID为可选填入内容)、用户名称(username)(也是可选项，给后续的需求提供帮助)，针对每一个需要输入的位置都做一个圆圈叹号提示，告知用户各个内容需要在企业微信的何处获取
4.3.首页最底部生成一个免责声明一段话，例如用于个人测试、请多少时间内删除等等的声明，用于开发者免责
4.4.为用户ID为【root-admin】的用户提供一个预留该软件管理员的权限，后续系统内容根据管理员权限做更高可操作性，该用户密码第一次使用时需要设置，以及确认密码，以后每次这个用户登录需要提供密码登入系统，其他用户正常登入即可，该超级管理员用户不参与企业微信所有的接口调用，仅做本地程序的全部配置使用，可在配置时，进行一次增量的系统管理员添加，添加一个可参与企业微信交互的管理员
4.5.首页需要填写的内容：除首次填写外，后续可以提供可填入内容下拉选，根据【企业名称(corpname)(不许重复)】进行选择，或者所有内容可由【用户ID为【root-admin】的管理员用户】进行配置进行使用
4.6.首页提供用户操作手册说明位置，着重提示用户的一个点位为本机公网IP，该位置需要拾取到当前机器对应公网的IP，用户可复制内容，用于给予填写企业微信后台，授权可信任IP，以便后续调用接口授权，该内容可进行分号【;】分隔，可以在系统内进行一个增量的记录，去重配置限制在120个IP以内，如果系统内遇见如下错误，要将【from ip: 139.215.46.96】这个位置的IP进行增量记录，并一旦发现报错，就弹窗提示用户需要去指定的位置去进行配置企业微信可信任IP，如【https://work.weixin.qq.com/wework_admin/frame#apps/modApiApp】这个位置选择【xxx】应用，进行可信任IP配置
{
    "errcode": 60020,
    "errmsg": "not allow to access from your ip, hint: [1741842467591810604040261], from ip: 139.215.46.96, more info at https://open.work.weixin.qq.com/devtool/query?e=60020",
    "livingid_list": []
}
4.7.制作首页登入按钮，用户填写信息完全，或者选择信息完全后，可点击登入按钮进入系统，可在登入系统按钮触发的时候进行接口企业微信调用测试是否允许，可以测试出来如上的企业微信自建应用可信任IP是否需要重新填写，可以提示用户进行全量填写，并提示用户可以5分钟之后再次尝试登入
5.该系统所有方位企业微信接口位置都需要进行token的拉取，所以一开始就要记录好拉取的token，并后续每个接口访问都要前置token拉取，拉取token接口如下：
curl --location --request GET 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=ww098b22d822db00d7&corpsecret=gbKNpjiNwkNjyP53QCe6VnzIJUFFRokeVZ5xe6x707I&debug=1'
6.登入系统后，默认进入左侧第1个菜单，创建预约直播：
6.1.官方文档地址为【https://developer.work.weixin.qq.com/document/path/96837】
6.2.接口调用示例如下：
curl --location --request POST 'https://qyapi.weixin.qq.com/cgi-bin/living/create?access_token=nludLAAJZKA3idMG0W9Y0AJK0lRVWq9P6ty1a-6nv58IWZP7BAgczO9BTyMLZYUqVhbiTrfGWB9q-m0XjDMeaMJoAKLkLtiNoyvY-kKBDKraSn45kjhWDMcFztZvKksGzjfGzltg852TGNPQH3K7CtQBKNo-yryQ550VfdR5DhOeRvrHDXL-a4PzqeGWl59pZBbnrOX6pB3RHdNOD9sskw' \
--header 'Content-Type: application/json' \
--data-raw '{
   "anchor_userid": "WangDeSheng",
   "theme": "预约直播-企业->推广2",
   "living_start": 1741846600,
   "living_duration": 3600,
   "description": "test description",
   "type": 3,
   "agentid" : 1000002
}'
6.3.如上接口示例，各参数说明：
6.3.1.直播用户ID：anchor_userid，可使用登入系统时填入的userid字段，如没有填写，则让用户自行填写，并增加圆圈叹号指引用户在何处可以获取
6.3.2.直播标题：theme，直播的标题，最多支持20个utf8字符
6.3.3.直播开始时间：living_start，直播开始时间的unix时间戳
6.3.4.直播持续时长：living_duration，直播持续时长
6.3.5.直播的开始时间和直播持续时长，可以做成一个可以选到秒级的时间组件，然后根据用户选择当前时间之后的时间，进行相关这两个字段填充
6.3.6.直播的类型：type，直播的类型，默认填写3：企业培训。如用户选择其他选项，则提示用户可能会创建直播失败或流程失败的提示。直播的类型，0：通用直播，1：小班课，2：大班课，3：企业培训，4：活动直播，默认 0。其中大班课和小班课仅k12学校和IT行业类型能够发起
6.3.8.直播的简介：description，直播的简介，最多支持100个utf8字符，仅对“通用直播”、“小班课”、“大班课”和“企业培训”生效
6.3.9.agentid，应用ID，根据系统登入时填入的内容进行填写
6.3.10.创建成功，如下，需将相关信息计入数据库,尤其是livingid，该直播ID字段很重要：
{
    "errcode": 0,
    "errmsg": "ok",
    "livingid": "lvd9BGagAAQPefP0y1nikU72QxxpmJVw"
}
6.3.11.如果直播创建成功，那么就需要紧接着在系统生成一个关于该直播的拉取详情任务，在创建完成10分钟后和直播开始时间+5分钟后2次进行的直播详情拉取任务，接口示例及返回结果示例如下：
官方接口文档地址：https://developer.work.weixin.qq.com/document/path/96835
接口请求示例：curl --location --request GET 'https://qyapi.weixin.qq.com/cgi-bin/living/get_living_info?access_token=nludLAAJZKA3idMG0W9Y0AJK0lRVWq9P6ty1a-6nv58IWZP7BAgczO9BTyMLZYUqVhbiTrfGWB9q-m0XjDMeaMJoAKLkLtiNoyvY-kKBDKraSn45kjhWDMcFztZvKksGzjfGzltg852TGNPQH3K7CtQBKNo-yryQ550VfdR5DhOeRvrHDXL-a4PzqeGWl59pZBbnrOX6pB3RHdNOD9sskw&livingid=lvd9BGagAAQPefP0y1nikU72QxxpmJVw&debug=1'
返回结果示例：{
    "errcode": 0,
    "errmsg": "ok",
    "living_info": {
        "theme": "预约直播-企业->推广2",
        "living_start": 1741839370,
        "living_duration": 143,
        "anchor_userid": "WangDeSheng",
        "main_department": 1,
        "viewer_num": 2,
        "comment_num": 3,
        "mic_num": 0,
        "open_replay": 0,
        "status": 2,
        "reserve_start": 1741846600,
        "reserve_living_duration": 3600,
        "description": "test description",
        "type": 0,
        "online_count": 0,
        "subscribe_count": 0
    }
}
返回结果说明：
参数说明：
errcode	返回码
errmsg	对返回码的文本描述内容
living_info	直播信息
living_info.theme	直播主题
living_info.living_start	直播开始时间戳
living_info.living_duration	直播时长，单位为秒
living_info.status	直播的状态，0：预约中，1：直播中，2：已结束，3：已过期，4：已取消
living_info.reserve_start	直播预约的开始时间戳
living_info.reserve_living_duration	直播预约时长，单位为秒
living_info.description	直播的描述，最多支持100个汉字
living_info.anchor_userid	主播的userid
living_info.main_department	主播所在主部门id
living_info.viewer_num	观看直播总人数
living_info.comment_num	评论数
living_info.mic_num	连麦发言人数
living_info.open_replay	是否开启回放，1表示开启，0表示关闭
living_info.replay_status	open_replay为1时才返回该字段。0表示生成成功，1表示生成中，2表示回放已删除，3表示生成失败
living_info.type	直播的类型，0：通用直播，1：小班课，2：大班课，3：企业培训，4：活动直播
living_info.push_stream_url	推流地址，仅直播类型为活动直播并且直播状态是待开播返回该字段
living_info.online_count	当前在线观看人数
living_info.subscribe_count	直播预约人数

6.3.12.创建完成成功后，跳转到第2个菜单，成员直播列表

7.左侧第2个菜单，成员直播列表
7.1.企业微信官方接口地址：https://developer.work.weixin.qq.com/document/path/96834
7.2.请求及返回参数示例：
curl --location --request POST 'https://qyapi.weixin.qq.com/cgi-bin/living/get_user_all_livingid?access_token=nludLAAJZKA3idMG0W9Y0AJK0lRVWq9P6ty1a-6nv58IWZP7BAgczO9BTyMLZYUqVhbiTrfGWB9q-m0XjDMeaMJoAKLkLtiNoyvY-kKBDKraSn45kjhWDMcFztZvKksGzjfGzltg852TGNPQH3K7CtQBKNo-yryQ550VfdR5DhOeRvrHDXL-a4PzqeGWl59pZBbnrOX6pB3RHdNOD9sskw' \
--header 'Content-Type: application/json' \
--data-raw '{
	"userid": "WangDeSheng",
	"cursor": "",
	"limit": 20
}'
参数说明：
参数	必须	说明
access_token	是	调用接口凭证
userid	是	企业成员的userid
cursor	否	上一次调用时返回的next_cursor，第一次拉取可以不填
limit	否	每次拉取的数据量，建议填20，默认值和最大值都为100

{
    "errcode": 0,
    "errmsg": "ok",
    "next_cursor": "",
    "livingid_list": [
        "lvd9BGagAAS8LrF_KrjKM9e9pibprzVQ",
        "lvd9BGagAAPFeXOvk0ffypqx89OxBVbQ",
        "lvd9BGagAAdnjTNDl7yDU9XZfNTyx8iA",
        "lvd9BGagAAeHpbboeHrUmRueoyLrympg",
        "lvd9BGagAAQPefP0y1nikU72QxxpmJVw",
        "lvd9BGagAAypY71o1zmnuZ4SwGGrQhNA"
    ]
}
参数说明：
errcode	返回码
errmsg	对返回码的文本描述内容
next_cursor	当前数据最后一个key值，如果下次调用带上该值则从该key值往后拉，用于实现分页拉取，返回空字符串代表已经是最后一页
livingid_list	直播ID列表

7.3.当前菜单内容，要做可查询列表，可根据成功创建的直播保存的信息，进行数据关联，可以根据保存的内容，进行搜索区域开发，合理设计，增加【列表导出】按钮，该页面需要分页处理数据
7.3.1.列表数据及涉及导出的列表名分别为：直播场次，直播开始时间，直播结束时间，主播信息，直播流量顶峰人数，直播流量顶峰时间，直播合计签到人数，直播合计签到次数等等
7.4.搜索区域的企业成员的userid字段，该字段如果不填写，那么就查询的本地SQLite中存储的内容，如果填写，就先进行本地数据查询，并可以点亮同步用户直播列表功能，该功能根据多个接口合成数据保存，分别涉及：获取用户直播列表【7.2】、【6.3.11】用户直播详情、获取直播观看明细(如下)，所有内容拉取完成后，保存到数据库内
获取直播观看明细企业微信官方接口地址：https://developer.work.weixin.qq.com/document/path/96836
curl --location --request POST 'https://qyapi.weixin.qq.com/cgi-bin/living/get_watch_stat?access_token=nludLAAJZKA3idMG0W9Y0AJK0lRVWq9P6ty1a-6nv58IWZP7BAgczO9BTyMLZYUqVhbiTrfGWB9q-m0XjDMeaMJoAKLkLtiNoyvY-kKBDKraSn45kjhWDMcFztZvKksGzjfGzltg852TGNPQH3K7CtQBKNo-yryQ550VfdR5DhOeRvrHDXL-a4PzqeGWl59pZBbnrOX6pB3RHdNOD9sskw' \
--header 'Content-Type: application/json' \
--data-raw '{
	"livingid": "lvd9BGagAAQPefP0y1nikU72QxxpmJVw",
	"next_key": ""
}'
参数说明：
参数	必须	说明
access_token	是	调用接口凭证
livingid	是	直播的id
next_key	否	上一次调用时返回的next_key，初次调用可以填"0"

{
    "errcode": 0,
    "errmsg": "ok",
    "stat_info": {
        "users": [],
        "external_users": [
            {
                "external_userid": "wmd9BGagAAcV672nvFb2SHGwFHKotxQg",
                "type": 1,
                "name": "万强",
                "watch_time": 38,
                "is_comment": 1,
                "is_mic": 0,
                "invitor_external_userid": "wmd9BGagAAImsTlYX4a4RGavhNT5LvEA"
            },
            {
                "external_userid": "wmd9BGagAAImsTlYX4a4RGavhNT5LvEA",
                "type": 1,
                "name": "黍离。",
                "watch_time": 52,
                "is_comment": 1,
                "is_mic": 0,
                "invitor_userid": "WangDeSheng"
            }
        ]
    },
    "ending": 1,
    "next_key": ""
}

参数说明：
参数	说明
errcode	返回码
errmsg	对返回码的文本描述内容
ending	是否结束。0：表示还有更多数据，需要继续拉取，1：表示已经拉取完所有数据。注意只能根据该字段判断是否已经拉完数据
next_key	当前数据最后一个key值，如果下次调用带上该值则从该key值往后拉，用于实现分页拉取
stat_info	统计信息列表
stat_info.users	观看直播的企业成员列表
stat_info.users.userid	企业成员的userid
stat_info.users.watch_time	观看时长，单位为秒
stat_info.users.is_comment	是否评论。0-否；1-是
stat_info.users.is_mic	是否连麦发言。0-否；1-是
stat_info.users.invitor_userid	邀请人的userid
stat_info.users.invitor_external_userid	邀请人的external_userid
stat_info.external_users	观看直播的外部成员列表
stat_info.external_users.external_userid	外部成员的userid
stat_info.external_users.type	外部成员类型，1表示该外部成员是微信用户，2表示该外部成员是企业微信用户
stat_info.external_users.name	外部成员的名称
stat_info.external_users.watch_time	观看时长，单位为秒
stat_info.external_users.is_comment	是否评论。0-否；1-是
stat_info.external_users.is_mic	是否连麦发言。0-否；1-是
stat_info.external_users.invitor_userid	邀请人的userid，邀请人为企业内部成员时返回（观众首次进入直播时，其使用的直播卡片/二维码所对应的分享人；仅“推广产品”直播支持）
stat_info.external_users.invitor_external_userid	邀请人的external_userid，邀请人为非企业内部成员时返回（观众首次进入直播时，其使用的直播卡片/二维码所对应的分享人；仅“推广产品”直播支持）

这个位置，要获取相关用户名称的时候，如下：
7.4.1.首先，如果获取直播观看明细企业微信官方接口内进行了返回，则使用官方返回的名称
7.4.2.如果邀请人ID相关字段和直播的创建新信息相同，则就认定为直播创建人邀请的，直接使用直播创建人名称即可，可以回头在创建直播【6.3.1】中增加一个入参，为创建直播用户名称，不用传递给企业微信，仅做数据库记录即可
7.4.3.可以从stat_info统计信息列表中分别分析当前邀请人id是否存在于整个结果数据中，如果有，那么就根据遍历到的哪个数据的名称即可认定为邀请人名称，请注意，别搞成了自己邀请自己哟
7.4.4.如果都获取不到，那么请从数据库、缓存、等等取用
7.4.5.如果仍然取不到，那么请使用官方接口获取，但可能会出现没有权限、报错等等，请不要耽误整体流程，可以友好提示用户去开通权限，然后记录字段为空字符串即可

7.5.成员直播列表，每行数据增加【查看明细】、【导入签到信息】、【取消预约直播】、【导出】4个按钮，该列表也需要分页
7.5.1.【查看明细】，跳转到新的页面，当前页面显示拉回的该直播的企业微信直播详情信息，以及导入的签到信息关联起来的信息，每次进入该页面都要进行一次远程企业微信直播信息拉取，并合并回本地数据库，直播、用户详情相关数据的列表查询以及导出Excel，导出数据分别为：直播场次，直播的开始、结束时间，主播信息，观看直播的用户信息(用户名称，首次进入直播间时间，分段进入直播间时间，观看直播时间合计，分计观看时间，签到次数合计，分计签到时间，邀请人名称，、以及其他等等数据库有的字段信息，如信息无法获取的，则不进行设计显示了
7.5.2.详情上部位置需要制作搜索区域，可根据数据库已有字段信息，进行搜索设计
7.5.3.页面新增【导入签到信息】、【取消预约直播】、【导出】3个按钮
7.5.4.[导入签到信息]为1个Excel，但会有多个sheet，需要根据导入的数据表格进行分析，然后对应进行数据合并进入直播明细，进行到这块的时候，可以让我提供给你已有的签到信息Excel，然后你按照这个分析
第一个sheet页：第一次签到
签到统计	
签到发起时间	已签到人数
2025.3.13 12:17	2
	
签到明细	
已签到成员	所在部门
黍离。@微信	-
万强@微信	-

7.5.5.【导出】功能按钮，同【7.5.1】，根据数据库数据合理设计出哪些字段导出哪些保留
7.5.6.直播详情信息依然要分页处理数据，另外，在整个页面的最下面，做一些用户画像分析
7.5.7.【取消预约直播】官方文档：https://developer.work.weixin.qq.com/document/path/96838
请求方式： POST（HTTPS）
请求地址： https://qyapi.weixin.qq.com/cgi-bin/living/cancel?access_token=ACCESS_TOKEN

请求包体：

{
   "livingid": "XXXXXXXXX"
}
返回包体：
{
   "errcode": 0,
   "errmsg": "ok"
}

7.6.每个导出数据的第二个sheet页，分别做相关导出图表分析功能，用以用户画像(该导出为可选功能导出)


8.增加左侧第3个菜单，配置及设置，一个设置页面，根据系统超级管理员、企微管理员和普通用户进行相关设置信息配置，如企业信息配置，如各登录系统等级用户配置、如数据库文件保存位置、如数据库数据按日期清理，如日志信息保存位置等等按权限设计内容

9.开发的系统架构尽量轻量，减少用户企业资金负担以及维护成本，设计功能要便于管理员操作，尽可能的一键完成，并且要尽可能能在管理后台或企业微信上都可以操作，在轻量化的基础上，要保证质量，减少宕机等异常情况发生，也要保证程序员入手快速

10.要控制好商用版权，个人隐私协议等等的法律法规遵守，更合理合法的做出系统

11.增加超级管理员的忘记密码处理能力，基于开发人员一些便捷后门

12.第一次使用应用程序，给用户提供一下引导性初始化配置功能页面，进行友好的初始化配置

















