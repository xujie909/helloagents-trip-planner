<template>
  <div class="guide-root">
    <div class="guide-banner">
      <span class="guide-banner-seal">书</span>
      <div><h1>使用手记</h1><p>知行旅行 · 功能指南</p></div>
    </div>

    <!-- 六大板块详解 -->
    <div class="guide-detail">
      <!-- 首页 -->
      <div class="gd-section">
        <div class="gd-head"><span class="gd-seal">家</span><h3>🏠 首页 — 你的旅行起点</h3></div>
        <div class="gd-body">
          <h4>📌 做什么的</h4>
          <p>首页是你登录后看到的第一个页面，汇集了<strong>实时天气、位置信息、AI生活建议</strong>和<strong>个人旅行数据统计</strong>，是了解旅行环境和自身旅行足迹的仪表盘。</p>
          <h4>🪜 怎么用</h4>
          <ol>
            <li><strong>查看天气</strong>：点击「所在」卡片可手动设置城市，系统自动获取该城市的实时天气、温度、湿度数据</li>
            <li><strong>AI生活建议</strong>：右下角 🤖 按钮会根据当前城市的天气温度自动生成实用建议（如「下午热，多喝水防中暑」），点击可刷新</li>
            <li><strong>填写旅行档案</strong>：右侧栏「旅行档案」卡片，填写你的性别、年龄、旅行动机、习惯、同行偏好，AI推荐会更精准</li>
            <li><strong>快捷入口</strong>：点击「旅行顾问」「行程规划」「行囊记录」可直接跳转到对应功能</li>
          </ol>
        </div>
      </div>

      <!-- 旅行顾问 -->
      <div class="gd-section">
        <div class="gd-head"><span class="gd-seal">谈</span><h3>💬 旅行顾问 — 你的AI旅行参谋</h3></div>
        <div class="gd-body">
          <h4>📌 做什么的</h4>
          <p>一个<strong>AI对话助手</strong>，接入高德地图真实数据，可以回答任何旅行相关问题——目的地推荐、景点介绍、路线查询、美食住宿建议、季节穿搭提醒等。支持<strong>流式输出</strong>（逐字显示）和<strong>语音输入</strong>。</p>
          <h4>🪜 怎么用</h4>
          <ol>
            <li><strong>直接提问</strong>：在底部输入框输入问题，如「夏天带孩子去哪玩」「北京三日游怎么安排」「杭州有什么必去景点」</li>
            <li><strong>语音输入</strong>：点击输入框左侧 🔊 开启语音模式，再点 🎤 说话，说完自动发送</li>
            <li><strong>多轮对话</strong>：左侧面板管理对话，点击「＋ 新对话」开启新话题，可切换查看历史对话</li>
            <li><strong>地图查看</strong>：当顾问获取到景点数据时，顶部会出现「🗺️ 查看地图」按钮，点击展示交互式地图</li>
          </ol>
        </div>
      </div>

      <!-- 行程规划 -->
      <div class="gd-section">
        <div class="gd-head"><span class="gd-seal">划</span><h3>✈️ 行程规划 — 一键生成完整旅行计划</h3></div>
        <div class="gd-body">
          <h4>📌 做什么的</h4>
          <p>填写目的地、日期和偏好，系统会调用<strong>四个AI智能体并行工作</strong>——景点搜索Agent、天气查询Agent、酒店推荐Agent、行程规划Agent——自动生成包含每日行程、景点安排、餐饮推荐、酒店住宿、天气预报和预算汇总的<strong>完整旅行计划</strong>。</p>
          <h4>🪜 怎么用</h4>
          <ol>
            <li><strong>填写信息</strong>：输入目的地城市、出发和结束日期（自动计算天数）</li>
            <li><strong>设置偏好</strong>：选择交通方式（公交/自驾/步行/混合）、住宿偏好（经济/舒适/豪华/民宿）、旅行偏好（历史/自然/美食/购物/艺术/休闲）</li>
            <li><strong>额外要求</strong>：在文本框中补充特殊需求（如「对海鲜过敏」「需要无障碍设施」）</li>
            <li><strong>生成计划</strong>：点击「🚀 生成旅行计划」，等待约30-60秒，系统自动调用多Agent并行处理</li>
            <li><strong>结果操作</strong>：生成后可在结果页查看每日行程、导出PDF/图片，点击「💾 保存行程」存入行囊记录</li>
          </ol>
        </div>
      </div>

      <!-- 行囊记录 -->
      <div class="gd-section">
        <div class="gd-head"><span class="gd-seal">囊</span><h3>📋 行囊记录 — 管理你的旅行日志</h3></div>
        <div class="gd-body">
          <h4>📌 做什么的</h4>
          <p>存储和管理所有已保存的旅行计划。支持查看<strong>景点详细介绍</strong>（AI生成+高德真实数据）、<strong>任务清单</strong>追踪完成进度、<strong>旅行笔记</strong>书写感悟、上传图片视频语音附件。</p>
          <h4>🪜 怎么用</h4>
          <ol>
            <li><strong>查看行程</strong>：点击「查看」打开行程详情，顶部分页标签切换「行程概览」「行程手札」「笔记」「景点介绍」</li>
            <li><strong>景点介绍</strong>：点击景点名（蓝色链接），AI自动生成800字以上详细介绍，包含基本概况、建筑特色、文化内涵、游玩亮点、周边推荐、出行提示</li>
            <li><strong>任务清单</strong>：在「行程手札」页，勾选 ✅ 标记完成，拖动排序，修改名称和花费，添加删除条目。全部完成后可「📊 发送到数据广场」</li>
            <li><strong>旅行笔记</strong>：点击「🖊️ 写笔记」打开备忘录，支持横线纸书写体验，可上传图片、视频、录音附件</li>
          </ol>
        </div>
      </div>

      <!-- 旅行导览 -->
      <div class="gd-section">
        <div class="gd-head"><span class="gd-seal">导</span><h3>🧭 旅行导览 — 实时GPS语音导游</h3></div>
        <div class="gd-body">
          <h4>📌 做什么的</h4>
          <p>选择已保存的行程后，开启<strong>实时GPS追踪</strong>模式。后台自动预加载所有景点的<strong>语音介绍</strong>，当用户靠近景点时自动语音播报。支持<strong>交互式地图</strong>显示用户位置和景点标记。</p>
          <h4>🪜 怎么用</h4>
          <ol>
            <li><strong>选择行程</strong>：在旅行导览页选择一个未完成的行程（只显示有未完成景点的行程）</li>
            <li><strong>授权GPS</strong>：点击「🔓 开启GPS定位」允许浏览器获取位置（手机上会自动弹出授权弹窗）</li>
            <li><strong>自动导览</strong>：距景点500米时语音提醒「您距离XX还有350米」，到达后自动播放景点详细介绍</li>
            <li><strong>地图查看</strong>：交互式高德地图显示蓝色圆点（你的位置）和红色圆点（景点位置），可缩放拖拽</li>
            <li><strong>任务同步</strong>：到达景点后自动在行囊记录中标记为已完成 ✅</li>
          </ol>
        </div>
      </div>

      <!-- 数据广场 -->
      <div class="gd-section">
        <div class="gd-head"><span class="gd-seal">数</span><h3>📊 数据广场 — 万千行者的旅行数据</h3></div>
        <div class="gd-body">
          <h4>📌 做什么的</h4>
          <p>汇集<strong>14万条</strong>真实旅行行为数据。通过饼图和统计列表展示各省份旅行热度，支持<strong>省份→城市→景点</strong>三级下钻查询。底部数据洞察根据季节、性别、年龄分析旅行偏好。顶部搜索框可快速查找目的地。</p>
          <h4>🪜 怎么用</h4>
          <ol>
            <li><strong>浏览热度</strong>：饼图展示各省份旅行人次，点击扇区或列表项进入省份详情</li>
            <li><strong>三级下钻</strong>：省份页显示各城市/区域统计 → 点击城市查看热门景点排名</li>
            <li><strong>数据洞察</strong>：底部卡片展示当前季节推荐、男女偏好差异、不同年龄段喜好</li>
            <li><strong>搜索</strong>：顶部搜索框输入城市或景点名，快速定位并跳转到对应统计</li>
            <li><strong>同步数据</strong>：在行囊记录中完成全部任务后，点击「发送到数据广场」贡献你的旅行数据</li>
          </ol>
        </div>
      </div>
    </div>

    <!-- 小贴士 -->
    <div class="guide-tips">
      <span class="tips-icon">💡</span>
      <div>
        <h4>使用小贴士</h4>
        <ul>
          <li>语音功能仅支持 <strong>Chrome / Edge</strong> 浏览器</li>
          <li>旅行导览在<strong>手机上</strong>使用体验最佳（GPS精确定位）</li>
          <li>景点介绍首次生成后<strong>缓存7天</strong>，再次查看不消耗token</li>
          <li>首页右侧栏完善<strong>个人档案</strong>后，AI推荐会更精准</li>
          <li>数据广场的<strong>搜索框</strong>可直接查找省份、城市或景点</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<style scoped>
.guide-root { padding: 32px 40px; max-width: 900px; margin: 0 auto; animation: viewIn .35s ease-out both }
@keyframes viewIn { from{opacity:0;transform:scale(.98) translateY(6px)} to{opacity:1;transform:scale(1) translateY(0)} }

.guide-banner { display: flex; align-items: center; gap: 16px; padding: 28px 32px; background: linear-gradient(135deg, #fdf5ee, #fef9f4); border: 1px solid #e8d0bf; border-radius: 18px; margin-bottom: 32px; box-shadow: 0 2px 12px rgba(139,69,19,.04) }
.guide-banner-seal { width: 48px; height: 48px; border-radius: 8px; background: #c43b3b; color: #faf0d7; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: 900; font-family: 'STKaiti','楷体','KaiTi',serif }
.guide-banner h1 { font-size: 24px; font-weight: 700; color: #5c3a21; margin: 0; font-family: 'STKaiti','楷体','KaiTi',serif }
.guide-banner p { font-size: 14px; color: #b8a088; margin: 2px 0 0 }

/* 板块详解 */
.guide-detail { display: flex; flex-direction: column; gap: 20px; margin-bottom: 28px }
.gd-section { background: #fff; border: 1px solid #eadccf; border-radius: 18px; overflow: hidden; transition: all .2s }
.gd-section:hover { box-shadow: 0 3px 14px rgba(139,69,19,.06) }
.gd-head { display: flex; align-items: center; gap: 12px; padding: 18px 24px; background: #faf7f2; border-bottom: 1px solid #eadccf }
.gd-seal { width: 28px; height: 28px; border-radius: 5px; background: #c43b3b; color: #faf0d7; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 900; font-family: 'STKaiti','楷体','KaiTi',serif; flex-shrink: 0 }
.gd-head h3 { font-size: 17px; font-weight: 700; color: #5c3a21; margin: 0; font-family: 'STKaiti','楷体','KaiTi',serif }
.gd-body { padding: 20px 24px }
.gd-body h4 { font-size: 15px; font-weight: 700; color: #6b5344; margin: 16px 0 8px }
.gd-body h4:first-child { margin-top: 0 }
.gd-body p { font-size: 14px; color: #6b5344; line-height: 1.9; margin: 0 0 12px }
.gd-body strong { color: #c43b3b }
.gd-body ol { margin: 0; padding-left: 20px }
.gd-body li { font-size: 14px; color: #6b5344; line-height: 2 }
.gd-body li strong { color: #5c3a21 }

/* 小贴士 */
.guide-tips { display: flex; gap: 16px; padding: 22px 28px; background: linear-gradient(135deg, #fdf0e8, #fef5ec); border: 1px solid #f0c080; border-radius: 16px }
.tips-icon { font-size: 28px; flex-shrink: 0 }
.guide-tips h4 { font-size: 16px; font-weight: 700; color: #8b4513; margin: 0 0 8px; font-family: 'STKaiti','楷体','KaiTi',serif }
.guide-tips ul { margin: 0; padding-left: 18px }
.guide-tips li { font-size: 14px; color: #6b5344; line-height: 2 }
.guide-tips strong { color: #c43b3b }

@media (max-width: 767px) { .guide-root { padding: 16px } .gd-body { padding: 16px } }
</style>
