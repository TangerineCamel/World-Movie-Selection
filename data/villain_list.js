// 反派影评·十年十佳系列
// 结构：VILLAIN_DATA[专场key] = { label:'专场名', films:[...] }
// 切换专场 = 切 key（类似电影手册切年份）
// poster 用完整 OSS URL（和其他榜单一致）
var VILLAIN_DATA = {
  cannes: {
    label: '戛纳专场',
    films: [
      { rank:1,  tmdb_id:254736, title_cn:'一千零一夜第1部：不安之人', director:'米格尔·戈麦斯',       year:2015, poster:'https://world-movie-selection.oss-cn-shanghai.aliyuncs.com/posters/254736.jpg' },
      { rank:2,  tmdb_id:457193, title_cn:'破败工厂',                  director:'佩德罗·皮诺',         year:2017, poster:'https://world-movie-selection.oss-cn-shanghai.aliyuncs.com/posters/457193.jpg' },
      { rank:3,  tmdb_id:186975, title_cn:'历史的终结',                director:'拉夫·迪亚兹',         year:2013, poster:'https://world-movie-selection.oss-cn-shanghai.aliyuncs.com/posters/186975.jpg' },
      { rank:4,  tmdb_id:103328, title_cn:'神圣车行',                  director:'莱奥·卡拉克斯',       year:2012, poster:'https://world-movie-selection.oss-cn-shanghai.aliyuncs.com/posters/103328.jpg' },
      { rank:5,  tmdb_id:329712, title_cn:'市场法则',                  director:'史蒂芬·布塞',         year:2015, poster:'https://world-movie-selection.oss-cn-shanghai.aliyuncs.com/posters/329712.jpg' },
      { rank:6,  tmdb_id:371865, title_cn:'玛·鲁特',                   director:'布鲁诺·杜蒙',         year:2016, poster:'https://world-movie-selection.oss-cn-shanghai.aliyuncs.com/posters/371865.jpg' },
      { rank:7,  tmdb_id:53413,  title_cn:'安吉里卡奇遇',              director:'曼努埃尔·德·奥利维拉', year:2010, poster:'https://world-movie-selection.oss-cn-shanghai.aliyuncs.com/posters/53413.jpg' },
      { rank:8,  tmdb_id:73532,  title_cn:'勒阿弗尔',                  director:'阿基·考里斯马基',     year:2011, poster:'https://world-movie-selection.oss-cn-shanghai.aliyuncs.com/posters/73532.jpg' },
      { rank:9,  tmdb_id:265228, title_cn:'廷巴克图',                  director:'阿伯德拉马纳·希萨柯', year:2014, poster:'https://world-movie-selection.oss-cn-shanghai.aliyuncs.com/posters/265228.jpg' },
      { rank:10, tmdb_id:396461, title_cn:'银湖之底',                  director:'大卫·罗伯特·米切尔', year:2018, poster:'https://world-movie-selection.oss-cn-shanghai.aliyuncs.com/posters/396461.jpg' },
    ]
  }
  // 以后加专场：
  // , oscar: { label:'奥斯卡专场', films:[ ... ] }
  // , venice_berlin: { label:'威尼斯混柏林', films:[ ... ] }
};
