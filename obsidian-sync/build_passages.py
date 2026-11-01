# -*- coding: utf-8 -*-
"""为每一组词生成「小短文」种子数据（passages.json）。

每篇必须覆盖该组全部 30 词（校验见 check_passages.py）。
写作约定：A2-B1 难度、130-190 词、一句话一个场景、目标词用原形或常见变形。
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "passages.json")

P = []

def add(g, title, hook, en, zh):
    P.append({"g": g, "title": title, "hook": hook, "en": en.strip(), "zh": zh.strip()})

add(1, "The Green School",
    "「学校搞环保项目」一条线，把教育、环境、科技、政策四类词全串起来。",
    """Our school started a green project last term. The aim was simple: make the academic curriculum more practical. Teachers wanted to educate students about the environment, not just prepare them for a written assessment.

At first only a few pupils were motivated. Then a science class did some research on air pollution in the local community. Their analysis of the data gave clear evidence: the school used too much energy and produced too much carbon emission.

The head teacher asked an expert for advice. She said we should conserve every resource we could: turn off the lights, recycle paper and plastic, and buy efficient digital equipment. New technology helped a lot — one innovation cut our electricity bill by a third.

Students also developed a small garden. It became a place to learn about sustainable food and to improve their computer literacy at the same time, logging the data online.

The project had a real impact. It raised the standard of our science lessons and benefited the local economy, because we bought vegetables from nearby farms. But the biggest challenge was money. The school had to ask the government for a policy that would fund such projects for every individual school.

Two years later, students who finish the course get a qualification in environmental studies. "It taught me that one person can make a difference," said one of them.""",
    """我们学校上学期启动了一个绿色项目。目标很简单：让学术课程更实用。老师想让学生真正了解环境，而不只是为一次书面考核做准备。

起初只有少数学生有干劲。后来一个科学班对社区里的空气污染做了研究。他们对数据的分析给出了明确证据：学校用电太多，碳排放也太高。

校长向一位专家请教。她说我们应该节约每一种资源：关灯、回收纸张和塑料、购买节能的电子设备。新技术帮了大忙——一项创新就让电费降了三分之一。

学生还在校园里开辟了小菜园。那里既成了了解可持续食物的课堂，也顺手提高了他们的电脑操作能力，数据都记录在网上。

这个项目带来了实实在在的影响。它提高了科学课的标准，也让当地经济受益，因为蔬菜是从附近农场买的。但最大的挑战是钱——学校只能请政府出台政策，为每一所学校的这类项目提供资金。

两年后，修完这门课的学生能拿到一张环境研究的资格证书。「它让我明白，一个人也能带来改变。」其中一个学生这样说。""")

add(2, "Anna's Second Job: Her Health",
    "一个职场人「拼命工作→身体报警→调整生活」的转折，工作类和健康类词各归其位。",
    """Anna spent ten years building her career in a large company. Her employer paid a good salary, and last spring she got a promotion. She had friendly colleagues, and her profession gave her real expertise. But her workload grew, and she missed deadline after deadline. She was no longer productive, and she began to doubt whether she was still competent.

At her last interview she had promised to work harder, but her body had other plans. She could not sleep, and she noticed the first symptom of burnout. Her doctor warned her about obesity, heart disease and high blood pressure. "Your diet is poor and you get no exercise," he said. "Good nutrition and a healthy lifestyle matter more than a big salary."

Anna took the advice seriously. She started physical exercise three times a week and tried to keep a balance between work and rest. The treatment was simple — better food, more sleep, less stress — and it worked. Six months later her mental health had improved too.

She even thought about leaving and looking for employment elsewhere, but in the end she stayed and changed the way she worked. Now she gives talks about prevention in the office and about the healthcare her company should offer.

"I want to retire early," she says, "but I want to be healthy enough to enjoy it." """,
    """安娜在一家大公司花了十年打造自己的职业。雇主给她不错的薪水，去年春天她还升了职。同事关系融洽，这个行业也给了她真正的专业能力。但工作量越来越大，她一次又一次错过截止日期。她不再高产，也开始怀疑自己能不能胜任。

最后一次面试时她承诺会更努力，可身体另有打算。她睡不着觉，还发现自己出现了过劳的第一个症状。医生警告她肥胖、心脏病和高血压的风险。「你饮食很差，又不锻炼，」他说，「良好的营养和健康的生活方式，比高薪重要得多。」

安娜认真接受了建议。她开始每周锻炼三次，努力在工作与休息之间保持平衡。治疗很简单——吃得更好、睡得更多、压力更小——而且有效。半年后，她的心理健康也改善了。

她甚至想过离开，去别处找份工作，但最后她留下来，改变了工作方式。现在她在办公室讲预防，也讲公司应该提供怎样的医疗保健。

「我想早点退休，」她说，「但我得健康到能享受它。」""")

add(3, "From Village to City",
    "村庄变城市的二十年，城市、交通、文化三组词都挂在同一条时间线上。",
    """My grandparents grew up in a rural village. There was one bus a day, no hospital and no proper transport. Today that village is part of a fast-growing urban area, and the change has been enormous.

The population has doubled in twenty years. Young people migrate from the countryside to find work, and the city keeps expanding. New infrastructure — roads, water pipes, a train line — was built to serve them. A sports facility and a library opened near the old market, which is located in the centre, and local residents can now commute to work in half an hour.

But growth brings problems. The number of private vehicles has risen sharply, so traffic congestion is part of daily life. Pedestrians wait a long time at crossings, and the air is worse than before.

The city council is trying to protect the past while welcoming the future. A museum was built to preserve the local heritage and tradition, and a festival celebrates the diversity of the people who live here. The local media broadcast a programme about the old market, and the audience loved it. Companies advertise on the same channel, which worries some people: how much influence should they have? Even entertainment news is paid for by them.

A journalist published a long article about cultural identity. "A city is not only buildings," she wrote. "Its value lies in the culture that people share." That idea has gone global: the article was read in many countries.""",
    """我祖父母在一个乡村长大。那时一天只有一班公交，没有医院，也没有像样的交通。今天那个村子已经变成快速扩张的城区的一部分，变化巨大。

二十年里人口翻了一番。年轻人从乡下迁来找工作，城市不断扩张。新的基础设施——道路、水管、一条铁路——为他们而建。老市场附近开了体育设施和图书馆（老市场就位于市中心），当地居民现在半小时就能通勤上班。

但发展也带来问题。私家车数量猛增，交通拥堵成了日常。行人在路口要等很久，空气也比以前差。

市政委员会想在迎接未来的同时守住过去。他们建了一座博物馆来保护当地遗产和传统，还有一个节日庆祝居民的文化多样性。当地媒体播了一档关于老市场的节目，观众很喜欢。企业也在同一个频道做广告，这让一些人担心：它们该有多大影响力？连娱乐新闻都是它们出钱做的。

一位记者发表了一篇关于文化认同的长文。「城市不只是建筑，」她写道，「它的价值在于人们共享的文化。」这个观点已经传遍全球：这篇文章在许多国家被读到。""")

add(4, "A Trip on a Tight Budget",
    "「出发—住宿—购物—算账」的旅行流水账，旅行词和金钱词正好各就各位。",
    """Last summer my sister and I planned a journey to Italy. We had a tight budget, so we booked everything online weeks in advance.

Our itinerary was simple: three cities in ten days. Our first destination was a small town by the sea, which was full of tourists in August. We found cheap accommodation outside the centre and made a reservation at a small hotel. On the day of departure a storm delayed our flight, and on arrival we discovered that one bag of luggage had not travelled with us.

We did not let it spoil the adventure. A friendly guide showed us the old town, and we spent the morning sightseeing. The scenery from the hill was worth the climb. In the afternoon we went to explore the market, where I bought a small souvenir for my mother.

Shopping taught me a few lessons. I checked every receipt, because you need proof if you want a refund. I compared prices, asked for a discount, and once found a real bargain. But foreign currency confused me, and I paid too much for a coffee.

Back home, I added up my expense and looked at my income. I had spent more than I could afford. To avoid getting into debt, I used part of my saving to pay the bill. The trip was a luxury, but the memories were valuable. Now I check the price before I make a purchase, and I never forget that a good consumer reads the small print.""",
    """去年夏天我和姐姐计划去意大利旅行。预算很紧，所以我们提前几周就在网上把一切订好了。

行程很简单：十天三座城市。第一个目的地是海边的一个小镇，八月份满是游客。我们在市中心外面找到便宜的住宿，在一家小旅馆做了预订。出发那天一场暴风雨让航班延误，到达时又发现有一件行李没跟我们一起飞。

我们没让它毁了这次冒险。一位友善的导游带我们逛老城，上午我们去观光。从山上看下去的风景，值得爬这一趟。下午我们去逛市场，我给妈妈买了一个小纪念品。

购物给我上了几课。我每张收据都留着，因为想退款就得有凭证。我比价、要求打折，还有一次真淘到了便宜货。但外币把我绕晕了，一杯咖啡付了太多钱。

回家后我把开支加了一遍，又看了看收入。我花的钱超出了能负担的范围。为了不背上债务，我动用了一部分储蓄来付账。这趟旅行算是奢侈，但回忆很宝贵。现在我买东西前会先看价格，也记住了：聪明的消费者会读小字条款。""")

add(5, "Cooking Class on a Rainy Sunday",
    "从「做饭」吃到「饭后运动」，饮食词和休闲词靠一顿饭连起来。",
    """My favourite pastime is cooking, so last Sunday I joined a class on Chinese cuisine.

We had a small snack before class, because the teacher warned us that we would eat a lot. She gave us a recipe for roast duck with a sweet sauce. "The key ingredient is patience," she said, "and the spice and seasoning must be in balance." We learned to boil the soup first, then fry the vegetables quickly to keep the flavour fresh. Each of us got a large portion to taste, and by then my appetite had returned.

After lunch we talked about leisure. One student goes hiking every weekend; another prefers camping with her children. A third has a gym membership but admits she goes mostly for the fitness, not the recreation. Someone asked about the tennis tournament on Saturday, and we argued about whether competition makes sport better or worse. A volunteer from the centre told us about the sports equipment we could borrow.

Our teacher, whose hobby is amateur photography, said that a good dish is like a good photograph: it needs light, colour and rhythm. "You don't need much to relax," she said. "But you do need to digest your food before you run."

I went home with a full stomach and a new menu to try.""",
    """我最爱的消遣是做饭，所以上周日我报了一堂中国菜课。

上课前我们吃了点小零食，因为老师提醒我们会吃很多。她给了我们一份烤鸭配甜酱的食谱。「关键原料是耐心，」她说，「香料和调味品必须平衡。」我们学会了先煮汤，再快速煎炒蔬菜以保留风味。每人都分到一大份试吃，那时我的食欲已经回来了。

午饭后我们聊起了休闲。一个学生每个周末都去徒步；另一个更喜欢带孩子去露营。第三位有健身房会员卡，但承认自己去主要是为了身体素质，不是为了消遣。有人问起周六的网球锦标赛，我们争论竞争到底让运动更好还是更糟。中心的一位志愿者还介绍了可以借用的运动器材。

我们的老师业余爱好是摄影，她说一道好菜就像一张好照片：需要光、色彩和节奏。「放松不需要太多东西，」她说，「但跑步前你得先把饭吃消化了。」

我带着满满的胃和一张想试的新菜单回了家。""")

add(6, "The New Flat",
    "看房—租房—装修—心情，房子词和情绪词都发生在同一间屋子里。",
    """Last month my friend Leo moved into an apartment in a quiet suburb. The neighbourhood is friendly, and the balcony looks out over a small park.

The landlord wanted three months' rent in advance. Leo had to sign a contract as a tenant and show that he could still pay the mortgage on his old property. The flat came furnished, with a spacious living room, a cosy bedroom and enough furniture for two people. He spent a weekend decorating it, and the utility bills turned out to be lower than he expected.

I asked how he felt. "Honestly, I was anxious at first," he said. "Moving is stressful." But now he is confident about the future and in a good mood most days. He is generous with his time, patient with his noisy neighbours, and always honest about his feelings.

What I like most is his curiosity. He is curious about everything: the history of the building, the name of every plant in the park. He is optimistic by nature, though not naive. He is never pessimistic, but he is sensitive to criticism and gets frustrated when a plan fails. Even so, he is grateful for small things and enthusiastic about every new idea.

"Emotion is not weakness," he told me. "Being shy and being strong can live in the same person." """,
    """上个月我朋友里奥搬进了郊区一套公寓。街区很友善，阳台正对一个小公园。

房东要预付三个月房租。里奥得作为房客签合同，还要证明自己仍能付得起老房子的按揭。公寓带家具，客厅宽敞，卧室温馨，家具够两个人用。他花了一个周末装修，水电费也比他预想的低。

我问他感觉如何。「说实话，一开始我很焦虑，」他说，「搬家压力大。」但现在他对未来有信心，大多数日子心情都不错。他舍得花时间，对吵闹的邻居有耐心，对自己的感受也一向诚实。

我最喜欢的是他的好奇心。他对什么都好奇：这栋楼的历史、公园里每一株植物的名字。他天性乐观，但一点也不天真。他从不悲观，可对批评敏感，计划失败时会沮丧。即便如此，他对小事心怀感激，对每个新想法都充满热情。

「情绪不是软弱，」他告诉我，「害羞和坚强可以住在同一个人身上。」""")

add(7, "An Art Festival in the Rain",
    "天气是背景、艺术是主角，自然类词全成了舞台布景。",
    """The forecast said showers, but we went anyway. The festival takes place every year in a forest by the ocean, and the landscape there is unforgettable.

The morning was humid, with a light breeze from the sea. By noon the temperature had dropped and a heavy shower soaked everyone. Nobody minded: the rain is part of the experience, like the flood of colour on the stage.

An artist had built a sculpture from driftwood, and a gallery tent showed an exhibition of wildlife photography. A guide explained that several species in the area are protected, and that a long drought last summer had damaged the forest.

In the evening an orchestra played under a tent. The only instrument was a piano, but the melody was slow and the rhythm was almost like rain, and the performance made the audience silent. A young singer with real talent sang poetry set to music, and a writer read from a book of literature about the sea.

"Nature is the first artist," she said. "We only copy her."

I understood what she meant. The creative work we saw that day was inspired by weather, water and light. Art does not need a perfect climate; it needs attention.""",
    """天气预报说有阵雨，我们还是去了。这个节每年都在海边的森林里举办，那里的风景让人难忘。

早上很潮湿，海上吹来微风。到中午气温降了下来，一场大雨把所有人淋透。没人在意：雨就是体验的一部分，像舞台上涌动的色彩。

一位艺术家用浮木做了一件雕塑，一个画廊帐篷里办着野生动物摄影展。导游讲解说，这一带有几个物种受保护，而去年夏天的一场长期干旱损伤了森林。

傍晚，一支管弦乐队在帐篷下演奏。唯一的乐器是钢琴，但旋律很慢，节奏几乎像雨，演出让观众安静下来。一位真正有天赋的年轻歌手唱了谱成曲的诗歌，一位作家朗读了一本关于海洋的文学书。

「大自然才是第一位艺术家，」她说，「我们只是模仿她。」

我懂她的意思。那天我们看到的创作，灵感都来自天气、水和光。艺术不需要完美的气候，它需要的是专注。""")

add(8, "Grandma Goes Online",
    "老一辈学用平板，家庭词和网络词在「教与学」里相遇。",
    """My grandmother is eighty-two, and last year she decided to learn to use a tablet.

Her childhood was spent in a village with no telephone, and her upbringing was strict. She had never trusted a screen. But she missed her relatives who had moved abroad, and she wanted to see their faces.

My cousin set up the device for her. The hardware was cheap but reliable, and the software was simple. He made the text large, put her favourite photos on the home screen and showed her how to download an app. Then he helped her upload a short video of her garden. Within a week she had joined an online group of neighbours and old friends.

Now she uses the platform every morning. She argues with her brother about politics, forgives him by lunchtime, and respects his opinions more than she admits. Her generation grew up writing letters; for her, a network of friends used to mean people you could visit. Now it means a list of names on a small screen.

"Friendship needs contact," she says. "It doesn't matter whether it's a letter or a message."

She is careful about privacy and keeps her data secure, and she has learned that easy access is also a risk. She avoids the virtual world after nine o'clock, because she knows about addiction. And she insists that a companion online is never a substitute for an adult who visits in person. Her relationship with my cousin changed too: he is no longer just the boy who fixes her tablet, but her teacher and her friend, and he gives her real support when a new app confuses her.

She has lived alone since her divorce in 1975, and she says the tablet has made her days less quiet.""",
    """我奶奶八十二岁，去年她决定学着用平板。

她的童年在一个没有电话的村子里度过，家教很严。她从不相信屏幕。但她想念搬到国外的亲戚，想看看他们的脸。

我表弟帮她装好了设备。硬件便宜但可靠，软件也很简单。他把字号调大，把家人照片放在首页，教她怎么下载应用。然后他帮她上传了一段自家花园的短视频。一周之内，她就加入了一个由邻居和老朋友组成的在线群组。

现在她每天早上都用这个平台。她跟哥哥争论政治，午饭前就原谅了他，而且比他以为的更尊重他的观点。她那一代人是在写信中长大的；对她来说，朋友圈以前意味着可以上门拜访的人，现在意味着小屏幕上的一串名字。

「友谊需要联系，」她说，「是信还是消息，不重要。」

她很注意隐私，把数据保护得很安全，也明白了「随手就能访问」本身就是风险。九点以后她不碰虚拟世界，因为她知道上瘾这回事。她坚持认为，网上的伙伴永远代替不了一个真的上门来看她的成年人。她和表弟的关系也变了：他不再只是帮她修平板的男孩，而是她的老师，也是她的朋友——新应用把她弄糊涂时，他给她实实在在的支持。

1975 年离婚后她一直独居，她说这块平板让她的日子没那么安静。""")

add(9, "The Lantern Festival",
    "节庆的钱从哪来？把节日词和政府、公共服务词接在一起。",
    """Every autumn my city holds a festival that lasts four days. The council and the municipal government pay for part of it, and local businesses fund the rest.

The opening ceremony begins with a parade through the old streets. People wear traditional costume, and children carry lanterns. In the evening there are fireworks over the river, followed by a feast in the main square. For one night the whole centre feels like a carnival, and every gathering of neighbours turns into a party.

We celebrate the founding of the town with this festival: a short play each year commemorates the first families who arrived here. So it is also an anniversary for every family that has lived here for generations. There is a small memorial in the park, and an official from the authority lays a flower there each year. The ritual never changes, and that is exactly what people love about it.

Behind the fun there is real work. The council has to allocate a budget: part goes to public service such as cleaning and safety, part to a subsidy for local restaurants. A tax on hotel rooms helps pay for the decorations. The welfare of older residents is not forgotten — the pension fund for retired workers gets a small share.

Regulations control noise, traffic and the sale of alcohol. Some people complain about the cost, but most agree that the sector which benefits most is tourism. A festive street, they say, is a public good, and every custom is worth keeping.""",
    """每年秋天，我所在的城市都会办一个为期四天的节日。市政会和市政府出一部分钱，本地企业出资剩下的部分。

开幕式是穿过老街的游行。人们穿着传统服装，孩子提着灯笼。晚上河上有烟花，之后是在主广场的盛宴。有那么一夜，整个市中心像个狂欢节，每一场邻居的聚会都变成派对。

我们用这个节日来庆祝建城：每年一出短剧纪念最早来到这里的那几户人家。所以对每一户世代住在这里的人家来说，它也是周年纪念日。公园里有一座小纪念碑，每年当局的一位官员会在那里献花。仪式从不改变——而这正是人们喜欢它的原因。

热闹背后是实打实的工作。市政会得分配预算：一部分用于清洁、安保这类公共服务，一部分补贴本地餐馆。旅馆的房间税帮着支付装饰费用。老年居民的福利也没被忘记——退休职工的养老基金能分到一小份。

规章管理噪音、交通和酒类销售。有人抱怨花钱多，但多数人同意受益最大的行业是旅游业。他们说，一条有节日气氛的街道就是公共财富，每一种习俗都值得保留。""")

add(10, "A Witness Who Speaks Two Languages",
    "一场审判需要翻译，犯罪/法律词和语言学习词在同一间法庭里碰面。",
    """When a theft took place in a small shop, the only witness was a student from abroad. The police made an arrest the same day, and the case went to court. The young man was asked to give evidence, but his English was not fluent enough, so a lawyer arranged a bilingual interpreter for the trial.

The interpreter had learned language the hard way. At school she memorized long vocabulary lists, revised grammar every evening and worked on her pronunciation with a dictionary and a mirror. She read poetry to improve her comprehension and wrote a short translation of every news story she heard. "Revision is boring," she says, "but fluency is built on it."

In court she was careful. One word can change a sentence. The accused man said he was innocent; the shop owner said he was guilty. The interpreter translated both, and the judge listened to the accent in the recording as well.

The prisoner had already spent eight months in prison before the trial began, so the verdict mattered to him more than to anyone else. He was found not guilty, and the victim was told the reason. Later the judge praised the interpreter's professionalism. "A trial is about language as much as about crime," he said. "Punishment only works if people understand what is said."

The student still studies. He wants a career in law, and he knows that the criminal justice system needs people who can speak for those who cannot speak for themselves.""",
    """一家小店发生盗窃案时，唯一的目击者是个外国留学生。警方当天就逮捕了人，案子上了法庭。年轻人被要求作证，但英语不够流利，于是律师为审判安排了一位双语翻译。

这位翻译是用笨办法学的语言。上学时她背长长的词汇表，每天晚上复习语法，还对着词典和镜子练发音。她读诗来提高理解力，听过的每条新闻都写一段简短译文。「复习很枯燥，」她说，「但流利度就是这么练出来的。」

在法庭上她很谨慎。一个词就能改变一句话的意思。被告说自己无罪，店主说他有罪。她把两边的话都译了，法官还听了录音里的口音。

审判开始前，这名囚犯已经在监狱里待了八个月，所以判决对他来说比任何人都重要。他最终被判无罪，受害者被告知了理由。后来法官称赞了翻译的专业水准。「审判既关乎语言，也关乎罪行，」他说，「只有人们听懂了，惩罚才有意义。」

那个学生还在学。他想从事法律工作，他知道刑事司法系统需要有人替那些说不出话的人说话。""")

add(11, "The Fake Bag That Made the Headlines",
    "匿名爆料 → 丑闻 → 核查，消费广告词和新闻舆论词连成一条新闻链。",
    """Last month a journalist received an anonymous message. It said that a famous brand was selling counterfeit bags in its own retail stores, and that the retailer had hidden the truth for years.

At first nobody believed it. Then the paper published an editorial asking for proof, and the story became a headline for a week. The coverage was enormous. A scandal like this damages credibility, and the company's marketing team went silent. Its expenditure on advertising could not buy back public trust.

The evidence, however, was strong. A customer kept her receipt and her warranty, checked the serial number, and asked for a refund. The transaction appeared on her subscription account, and the coupon she had used had a different code from the one advertised in the campaign. A commercial on television promised "genuine leather"; the label on the merchandise said otherwise.

The company tried to persuade the public that the mistake was small. Its statement was not persuasive. Reporters began to verify every claim, and a rumour about a second factory started to circulate. There was no censorship that could stop it, and the paper had no bias: it simply printed the documents. Its circulation rose by ten percent.

The lesson is not that all advertising is false. It is that good journalism is objective: it checks, it questions, and it refuses propaganda. A brand is only worth what people believe about it — and belief, once lost, is hard to win back.""",
    """上个月，一位记者收到一条匿名消息。消息说某个知名品牌在自己的零售店里卖假包，而这家零售商把真相瞒了好几年。

起初没人相信。后来报纸发表社论要求证据，这条新闻成了整整一周的头条。报道量巨大。这样的丑闻会损害公信力，公司的市场团队一言不发。花在广告上的支出，买不回公众的信任。

然而证据很扎实。一位顾客留着收据和保修卡，查了序列号，要求退款。这笔交易出现在她的订阅账户里，她用的优惠券编号与活动广告里的不一样。电视上一支广告承诺「真皮」，而商品上的标签却不是这么写的。

公司试图让公众相信这只是个小失误，但它的声明并没有说服力。记者们开始逐条核实，关于第二家工厂的谣言也开始传播。没有审查能拦住它，报纸也没有偏见：它只是把文件登出来。发行量涨了百分之十。

这堂课不是「所有广告都是假的」，而是：好的新闻是客观的——它核查、它质疑、它拒绝宣传话术。一个品牌的价值，只等于人们对它的相信——而信任一旦丢了，就很难再赢回来。""")

# ---- 合并 Obsidian 里已经写好的「30 词短文」（第 12 组起）-------------------
# 组 1-11 写在上面的 P 里：那时笔记用的还是「5 个句子」，没有短文可解析。
# 组 12 起短文真源在 Obsidian（每日词汇/第NN-NN组.md），这里解析后覆盖同组，
# 避免同一篇短文既维护 md 又维护本脚本 —— 以后新增组只改笔记即可。
try:
    import obsidian_parse as _op
    _mine = _op.parse_passages(_op.list_vocab_files(_op.VAULT))
    _idx = {p["g"]: i for i, p in enumerate(P)}
    for _p in _mine:
        if _p["g"] in _idx:
            P[_idx[_p["g"]]] = _p
        else:
            P.append(_p)
    P.sort(key=lambda x: x["g"])
    print("从 Obsidian 同步短文 %d 篇（组 %s）" % (len(_mine), "、".join(str(p["g"]) for p in _mine)))
except Exception as _e:
    print("⚠️ 读取 Obsidian 短文失败（保留脚本内硬编码）：%s" % _e)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump({"version": 1, "passages": P}, f, ensure_ascii=False, indent=1)
print("写出 %d 篇 → %s" % (len(P), OUT))
