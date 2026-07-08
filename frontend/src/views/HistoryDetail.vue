<template>
  <div class="history-detail-page">
    <div class="history-detail-shell">
      <template v-if="detailTrip">
        <div class="detail-hero-panel">
          <div class="detail-page-topbar hero-topbar">
            <button class="detail-back-btn" @click="goBackToHistory">← 返回行囊记录</button>
            <div class="detail-page-heading hero-heading">
              <div class="detail-heading-badges">
                <span class="heading-badge">📍 {{ detailTrip.city || '待补充城市' }}</span>
                <span class="heading-badge soft">{{ detailTrip.start_date }}</span>
                <span class="heading-badge soft">{{ detailTrip.data?.days?.length || 0 }} 天旅程</span>
              </div>
              <h1>{{ detailTitle }}</h1>
              <p>{{ detailTasks.length }} 条行程手札 · {{ attractionCount }} 个景点 · {{ notesFiles.length }} 份附件</p>
            </div>
            <div class="detail-hero-aside">
              <div class="hero-aside-label">当前状态</div>
              <strong>{{ taskPct >= 100 ? '已基本就绪' : '继续完善中' }}</strong>
              <p>{{ detailBudget.is_over_budget ? '预算需要关注' : '预算与清单状态正常' }}</p>
            </div>
          </div>

          <div class="detail-summary-grid">
            <div class="summary-stat-card">
              <span>📆 行程天数</span>
              <strong>{{ detailTrip.data?.days?.length || 0 }} 天</strong>
              <p>已收录 {{ detailTasks.length }} 条行程手札</p>
            </div>
            <div class="summary-stat-card progress">
              <span>📜 手札进度</span>
              <strong>{{ taskDoneCnt }}/{{ detailTasks.length || 0 }}</strong>
              <p>{{ taskPct }}% 已完成</p>
            </div>
            <div class="summary-stat-card budget" :class="detailBudget.is_over_budget ? 'over' : 'save'">
              <span>💰 预算差额</span>
              <strong>{{ detailBudget.is_over_budget ? '+' : '-' }}{{ formatMoney(Math.abs(detailBudget.difference || 0)) }}</strong>
              <p>{{ budgetInsightText }}</p>
            </div>
            <div class="summary-stat-card prep">
              <span>🧳 行前准备</span>
              <strong>{{ checklistDoneCnt }}/{{ prepChecklist.length || 0 }}</strong>
              <p>{{ checklistPct }}% 已完成</p>
            </div>
          </div>

          <div class="detail-overview-strip">
            <div class="overview-pill">
              <span>📍 当前城市</span>
              <strong>{{ detailTrip.city || '待补充' }}</strong>
            </div>
            <div class="overview-pill">
              <span>💵 计划 / 实际</span>
              <strong>{{ formatMoney(detailBudget.total_planned) }} / {{ formatMoney(detailBudget.total_actual) }}</strong>
            </div>
            <div class="overview-pill">
              <span>📎 笔记附件</span>
              <strong>{{ notesFiles.length }} 份</strong>
            </div>
            <div class="overview-pill">
              <span>🏛️ 已收录景点</span>
              <strong>{{ attractionCount }} 个</strong>
            </div>
          </div>
        </div>
      </template>
      <div v-else class="detail-page-topbar">
        <button class="detail-back-btn" @click="goBackToHistory">← 返回行囊记录</button>
      </div>

      <div v-if="loading" class="attr-loading page-loading">
        <div class="think-seal">行</div>
        <div class="think-dots"><span></span><span></span><span></span></div>
        <p class="think-text">行知正在翻阅这趟旅程...</p>
      </div>

      <div v-else-if="!detailTrip" class="detail-missing-state">
        <div class="empty-seal">囊</div>
        <p class="empty-title">没有找到这条旅行记录</p>
        <p class="empty-desc">它可能已被删除，或者链接已经失效。</p>
        <button class="empty-btn" @click="goBackToHistory">返回行囊记录</button>
      </div>

      <template v-else>
        <div class="detail-trip-ops">
          <div class="detail-trip-ops-main">
            <span class="detail-trip-ops-kicker">当前旅程</span>
            <strong>{{ currentTripStatusTitle }}</strong>
            <p>{{ currentTripStatusDesc }}</p>
          </div>
          <div class="detail-trip-ops-actions">
            <button class="detail-trip-ops-btn primary" @click="setTripAsCurrent">设为当前旅程</button>
            <button class="detail-trip-ops-btn" @click="detailTab='today'">打开今日行程</button>
            <button class="detail-trip-ops-btn" @click="openTripRecapVideo">生成回顾视频</button>
            <button class="detail-trip-ops-btn" @click="copyShareSummary">复制分享摘要</button>
          </div>
        </div>

        <div v-if="tripActionFeedback" :class="['trip-action-feedback', tripActionFeedback.type]">
          <div class="trip-action-feedback-main">
            <strong>{{ tripActionFeedback.title }}</strong>
            <p>{{ tripActionFeedback.description }}</p>
          </div>
          <button v-if="tripActionFeedback.tripId" class="trip-action-feedback-btn" @click="openTripDetail(tripActionFeedback.tripId)">
            打开这条旅行记录
          </button>
        </div>

        <div class="detail-tabs sticky-tabs">
          <div :class="['dt-tab',{active:detailTab==='today'}]" @click="detailTab='today'">☀️ 今日行程</div>
          <div :class="['dt-tab',{active:detailTab==='itinerary'}]" @click="detailTab='itinerary'">📋 行程概览</div>
          <div :class="['dt-tab',{active:detailTab==='tasks'}]" @click="detailTab='tasks'">📜 行程手札</div>
          <div :class="['dt-tab',{active:detailTab==='budget'}]" @click="detailTab='budget'">💰 预算</div>
          <div :class="['dt-tab',{active:detailTab==='prep'}]" @click="detailTab='prep'">🧳 出发前清单</div>
          <div :class="['dt-tab',{active:detailTab==='notes'}]" @click="detailTab='notes'">📝 笔记</div>
          <div :class="['dt-tab',{active:detailTab==='attraction'}]" @click="detailTab='attraction'" v-if="attrName">🏛️ {{ attrName }}</div>
        </div>

        <div class="detail-focus-panel">
          <div class="detail-focus-main">
            <span class="detail-focus-label">当前查看</span>
            <strong>{{ activeTabMeta.title }}</strong>
            <p>{{ activeTabMeta.description }}</p>
          </div>
          <div class="detail-focus-shortcuts">
            <button
              v-for="item in tabShortcutCards"
              :key="item.key"
              :class="['detail-shortcut-card', { active: detailTab === item.key }]"
              @click="detailTab = item.key"
            >
              <span class="detail-shortcut-top">{{ item.icon }} {{ item.title }}</span>
              <strong>{{ item.value }}</strong>
              <p>{{ item.hint }}</p>
            </button>
          </div>
        </div>

        <div class="detail-page-content">
          <div v-if="detailTab==='today'" class="today-panel">
            <div class="today-panel-head">
              <div>
                <h4>☀️ 今日行程 / 执行模式</h4>
                <p>{{ todayPanelDescription }}</p>
              </div>
              <div class="today-day-switcher">
                <button class="today-day-btn" :disabled="todayTripIndex<=0" @click="switchTodayDay(todayTripIndex - 1)">← 上一天</button>
                <span class="today-day-label">{{ todayDayLabel }}</span>
                <button class="today-day-btn" :disabled="todayTripIndex>=dayOptions.length-1" @click="switchTodayDay(todayTripIndex + 1)">下一天 →</button>
              </div>
            </div>

            <div class="today-top-grid">
              <div class="today-card primary">
                <span class="today-card-kicker">今日重点</span>
                <strong>{{ todayAttractionNames.length ? todayAttractionNames.join(' · ') : '今天先把任务和补给安排清楚' }}</strong>
                <p>{{ todayDayData?.description || todayDayData?.title || '如果今天没有精确日期匹配，就把它当作当前推进中的一天。' }}</p>
              </div>
              <div class="today-card status">
                <span class="today-card-kicker">执行进度</span>
                <strong>{{ todayDoneCount }}/{{ todayTasks.length || 0 }}</strong>
                <p>{{ todayTasks.length ? `今天已有 ${todayDoneCount} 项完成，剩余 ${todayRemainingCount} 项待推进。` : '今天还没有拆出独立任务，可先去行程手札补充。' }}</p>
              </div>
              <div class="today-card budget">
                <span class="today-card-kicker">今日预算</span>
                <strong>{{ formatMoney(todayPlannedCost) }} / {{ formatMoney(todayActualCost) }}</strong>
                <p>{{ todayBudgetHint }}</p>
              </div>
            </div>

            <div class="today-actions-grid">
              <button class="today-action-btn accent" @click="detailTab='tasks'">去勾选任务 / 记花费</button>
              <button class="today-action-btn" @click="detailTab='budget'">查看预算差额</button>
              <button class="today-action-btn" @click="detailTab='prep'">检查出发前清单</button>
              <button class="today-action-btn" @click="openTripRecapVideo">生成回顾视频</button>
              <button class="today-action-btn" @click="copyShareSummary">复制今日摘要</button>
            </div>

            <div v-if="todayTasks.length" class="today-task-list">
              <div v-for="task in todayTasks" :key="task.id" :class="['today-task-card', { done: task.done }]">
                <div class="today-task-main">
                  <div class="today-task-meta">
                    <span class="today-task-type">{{ typeIcon(task.type) }}</span>
                    <strong>{{ task.name || '未命名任务' }}</strong>
                    <span class="today-task-day">{{ task.day || todayDayShortLabel }}</span>
                  </div>
                  <p>{{ task.done ? '这项今天已经完成。' : '还可以继续推进，完成后会同步到预算和进度。' }}</p>
                  <div class="today-task-costs">
                    <span>计划 {{ formatMoney(task.planned_cost || 0) }}</span>
                    <span>实际 {{ formatMoney(task.actual_cost || 0) }}</span>
                  </div>
                </div>
                <div class="today-task-actions">
                  <button class="today-mini-btn primary" @click="toggleTask(task)">{{ task.done ? '标记未完成' : '标记完成' }}</button>
                  <button class="today-mini-btn" @click="focusTaskBudget(task)">登记花费</button>
                </div>
              </div>
            </div>
            <div v-else class="panel-empty-state compact">
              <strong>今天还没有单独拆出的任务</strong>
              <p>你可以去“行程手札”里补一条任务，或者直接按行程概览推进景点安排。</p>
            </div>

            <div class="today-attraction-strip" v-if="todayAttractions.length">
              <span class="today-attraction-label">今日景点</span>
              <div class="attr-tags">
                <span v-for="a in todayAttractions" :key="a.name" class="attr-link" @click="openAttractionPage(a.name, detailTrip.city, a)">🏛️ {{ a.name }}</span>
              </div>
            </div>
          </div>

          <div v-if="detailTab==='itinerary'">
            <div v-for="(day, idx) in detailTrip.data.days" :key="idx" class="detail-day">
              <h4 class="day-title">📆 第{{ day.day_index + 1 }}天 · {{ day.date }}</h4>
              <p class="day-desc">{{ day.description || day.title || '这一天的安排已经准备好了，等你继续补充细节。' }}</p>
              <div class="day-section" v-if="day.attractions.length">
                <span class="section-label">🎯 景点：</span>
                <div class="attr-tags">
                  <span v-for="a in day.attractions" :key="a.name" class="attr-link" @click="openAttractionPage(a.name, detailTrip.city, a)">🏛️ {{ a.name }}</span>
                </div>
              </div>
              <div class="day-section" v-if="day.meals.length">
                <span class="section-label">🍽️ 餐饮：</span>
                <a-tag v-for="m in day.meals" :key="m.name" color="green">{{ m.type }}: {{ m.name }}</a-tag>
              </div>
            </div>
            <div class="detail-budget" v-if="detailTrip.data.budget">
              <h4>💰 预算</h4>
              <p>景点 ¥{{ detailTrip.data.budget.total_attractions }} | 酒店 ¥{{ detailTrip.data.budget.total_hotels }} | 餐饮 ¥{{ detailTrip.data.budget.total_meals }} | 交通 ¥{{ detailTrip.data.budget.total_transportation }}</p>
              <p class="budget-total">总计：<strong>¥{{ detailTrip.data.budget.total }}</strong></p>
            </div>
          </div>

          <div v-if="detailTab==='tasks'">
            <div class="task-header"><h4>📜 行程手札</h4><span class="task-progress-text">{{ taskDoneCnt }}/{{ detailTasks.length }} · {{ taskPct }}%</span></div>
            <div class="task-progress-bar"><div class="task-progress-fill" :style="{width:taskPct+'%'}"></div></div>
            <div class="panel-save-hint" :class="taskSaveState">{{ taskSaveText }}</div>
            <div v-if="!detailTasks.length" class="panel-empty-state">
              <strong>这趟旅程还没有预算项目</strong>
              <p>先添加景点、餐饮、酒店或其他支出项，预算页会自动帮你汇总。</p>
            </div>
            <div v-else class="task-list">
              <div class="task-cost-head">
                <span class="task-cost-head-day">日期</span>
                <span class="task-cost-head-name">项目</span>
                <span class="task-cost-head-price">计划</span>
                <span class="task-cost-head-price">实际</span>
              </div>
              <div v-for="(t,i) in detailTasks" :key="t.id" :class="['task-item',{done:t.done}]" draggable="true" @dragstart="dragIdx=i" @dragover.prevent @drop="dropTask(i)">
                <span class="task-drag-handle" title="拖动排序">⋮⋮</span>
                <span class="task-check" @click="toggleTask(t)">{{ t.done?'✅':'⬜' }}</span>
                <span class="task-type" @click="cycleType(t)">{{ typeIcon(t.type) }}</span>
                <input class="task-day-inp" :value="t.day" @change="e=>{t.day=(e.target as HTMLInputElement).value;autoSave()}"/>
                <input class="task-name-inp" :value="t.name" @change="e=>{t.name=(e.target as HTMLInputElement).value;autoSave()}" :class="{strike:t.done}"/>
                <div class="task-cost-wrap">
                  <span class="task-cost-label">¥</span>
                  <input class="task-cost" :value="t.planned_cost" @change="e=>{updPlannedCost(t,(e.target as HTMLInputElement).value);autoSave()}" type="number" min="0"/>
                </div>
                <div class="task-cost-wrap">
                  <span class="task-cost-label">¥</span>
                  <input class="task-cost" :value="t.actual_cost" @change="e=>{updCost(t,(e.target as HTMLInputElement).value);autoSave()}" type="number" min="0"/>
                </div>
                <span class="task-del" @click="detailTasks.splice(i,1);autoSave()">✕</span>
              </div>
            </div>
            <div class="task-add-row"><button class="task-add-btn" @click="addTask">＋ 添加一条</button></div>
            <button v-if="taskPct>=100&&!published" class="task-publish-btn" @click="publishToPlaza" :disabled="publishing">{{ publishing?'发送中...':'📊 发送到数据广场' }}</button>
            <div class="task-publish-done" v-if="published">✅ 已同步到数据广场</div>
          </div>

          <div v-if="detailTab==='budget'" class="budget-panel">
            <div class="budget-overview">
              <div class="budget-stat-card">
                <span class="budget-stat-label">计划预算</span>
                <strong>{{ formatMoney(detailBudget.total_planned) }}</strong>
              </div>
              <div class="budget-stat-card actual">
                <span class="budget-stat-label">实际花费</span>
                <strong>{{ formatMoney(detailBudget.total_actual) }}</strong>
              </div>
              <div class="budget-stat-card" :class="detailBudget.is_over_budget ? 'over' : 'save'">
                <span class="budget-stat-label">预算差额</span>
                <strong>{{ detailBudget.is_over_budget ? '+' : '-' }}{{ formatMoney(Math.abs(detailBudget.difference || 0)) }}</strong>
              </div>
            </div>
            <div class="budget-summary-note">
              <span>{{ budgetInsightText }}</span>
            </div>
            <div v-if="budgetHighlight" class="budget-highlight-card" :class="budgetHighlight.kind">
              <strong>{{ budgetHighlight.title }}</strong>
              <p>{{ budgetHighlight.description }}</p>
            </div>
            <div v-if="!detailTasks.length" class="panel-empty-state compact">
              <strong>还没有可统计的预算项目</strong>
              <p>去“行程手札”里添加一条任务，就能开始记录计划预算和实际花费。</p>
            </div>
            <div v-else class="budget-type-grid">
              <div v-for="item in budgetTypeCards" :key="item.key" class="budget-type-card">
                <div class="budget-type-head">
                  <span>{{ item.icon }} {{ item.label }}</span>
                  <span>{{ item.count }} 项</span>
                </div>
                <div class="budget-type-row">
                  <span>计划</span>
                  <strong>{{ formatMoney(item.planned) }}</strong>
                </div>
                <div class="budget-type-row">
                  <span>实际</span>
                  <strong>{{ formatMoney(item.actual) }}</strong>
                </div>
                <div class="budget-type-progress">
                  <div class="budget-type-progress-bar">
                    <div class="budget-type-progress-fill" :class="{over:item.actual>item.planned&&item.planned>0}" :style="{width: budgetUsageWidth(item.planned, item.actual)}"></div>
                  </div>
                  <span>{{ budgetUsageLabel(item.planned, item.actual) }}</span>
                </div>
              </div>
            </div>
            <p class="budget-inline-tip">预算金额直接在“行程手札”里改，这里会自动汇总。</p>
          </div>

          <div v-if="detailTab==='prep'" class="prep-panel">
            <div class="prep-header">
              <div>
                <h4>🧳 出发前清单</h4>
                <p>把证件、衣物、设备和出发前准备统一收在这里。</p>
              </div>
              <span class="prep-progress-pill">{{ checklistDoneCnt }}/{{ prepChecklist.length }} · {{ checklistPct }}%</span>
            </div>
            <div class="task-progress-bar"><div class="task-progress-fill" :style="{width:checklistPct+'%'}"></div></div>
            <div class="panel-save-hint" :class="prepSaveState">{{ prepSaveText }}</div>
            <div v-if="!prepChecklist.length" class="panel-empty-state compact">
              <strong>还没有出发前清单</strong>
              <p>你可以先手动添加一项，或者一键补齐一组常用清单。</p>
            </div>
            <div v-else class="prep-groups">
              <div v-for="group in groupedPrepChecklist" :key="group.category" class="prep-group-card">
                <button class="prep-group-head prep-group-toggle" @click="togglePrepGroup(group.category)">
                  <div>
                    <strong>{{ prepCategoryEmoji(group.category) }} {{ group.category }}</strong>
                    <span>{{ group.done }}/{{ group.items.length }} 已完成</span>
                  </div>
                  <div class="prep-group-toggle-meta">
                    <span class="prep-group-progress">{{ group.progress }}%</span>
                    <span class="prep-group-arrow">{{ isPrepGroupCollapsed(group.category) ? '＋' : '－' }}</span>
                  </div>
                </button>
                <div v-if="!isPrepGroupCollapsed(group.category)" class="prep-list">
                  <div v-for="item in group.items" :key="item.id" :class="['prep-item',{done:item.done}]">
                    <span class="task-check" @click="togglePrepItem(item)">{{ item.done ? '✅' : '⬜' }}</span>
                    <select class="prep-category-select" :value="item.category" @change="e=>{item.category=(e.target as HTMLSelectElement).value;autoSavePrep()}">
                      <option v-for="category in PREP_CATEGORY_OPTIONS" :key="category" :value="category">{{ category }}</option>
                    </select>
                    <input class="prep-name-inp" :value="item.name" @change="e=>{item.name=(e.target as HTMLInputElement).value;autoSavePrep()}" :class="{strike:item.done}" />
                    <span class="task-del" @click="removePrepItem(item.id)">✕</span>
                  </div>
                </div>
              </div>
            </div>
            <div class="prep-actions">
              <button class="task-add-btn prep-action-btn" @click="addPrepItem">＋ 添加一项</button>
              <button class="task-add-btn prep-action-btn" @click="addDefaultPrepItems">＋ 补一组常用清单</button>
            </div>
          </div>

          <div v-if="detailTab==='notes'">
            <div class="trip-info-panel">
              <div class="trip-info-head">
                <div>
                  <h4>🧭 旅程信息中枢</h4>
                  <p>把酒店、交通、票务、联系人和集合信息都收进这一处，随时可查。</p>
                </div>
                <button class="notes-edit-btn" @click="saveTripInfo" :disabled="tripInfoSaving">{{ tripInfoSaving ? '保存中...' : '保存旅程信息' }}</button>
              </div>
              <div class="trip-info-grid">
                <label class="trip-info-field">
                  <span>酒店 / 住宿</span>
                  <input v-model="tripInfoDraft.hotel" class="trip-info-input" placeholder="例如：西湖边客栈 / 房型 / 入住提醒" />
                </label>
                <label class="trip-info-field">
                  <span>交通安排</span>
                  <input v-model="tripInfoDraft.transport" class="trip-info-input" placeholder="例如：高铁 G123 / 接驳 / 租车信息" />
                </label>
                <label class="trip-info-field">
                  <span>票务信息</span>
                  <input v-model="tripInfoDraft.tickets" class="trip-info-input" placeholder="例如：景区门票、演出票、取票提醒" />
                </label>
                <label class="trip-info-field">
                  <span>联系人</span>
                  <input v-model="tripInfoDraft.contact" class="trip-info-input" placeholder="例如：酒店前台 / 导游 / 同行联系人" />
                </label>
                <label class="trip-info-field full">
                  <span>集合地点 / 特别提醒</span>
                  <textarea v-model="tripInfoDraft.meetingPoint" class="trip-info-textarea" placeholder="例如：早上 8:30 在东门集合，记得带身份证和雨具"></textarea>
                </label>
              </div>
              <div class="trip-info-inline-note">
                <span>{{ tripInfoHintText }}</span>
              </div>
            </div>

            <div class="notes-panel-head">
              <div>
                <h4>📝 旅行笔记</h4>
                <p>把这次出发路上的感受、图片和录音收在一起。</p>
              </div>
              <button class="notes-edit-btn" @click="openNotesEditor">✍️ 编辑笔记</button>
            </div>
            <div v-if="detailTrip.notes" class="detail-notes"><p>{{ detailTrip.notes }}</p></div>
            <div v-else class="panel-empty-state compact">
              <strong>还没有旅行笔记</strong>
              <p>点右上角“编辑笔记”，把路上的心情和见闻记录下来。</p>
            </div>
            <div v-if="detailTrip.images&&detailTrip.images.length" class="detail-images">
              <h4>🖼️ 旅行图片</h4>
              <div class="image-grid"><img v-for="(img,i) in detailTrip.images" :key="i" :src="img" class="detail-img" @click="previewImage=img;previewVisible=true"/></div>
            </div>
            <div v-if="notesFiles.length" class="detail-files-section">
              <h4>📎 附件</h4>
              <div class="attach-list page-attach-list">
                <div v-for="(f,i) in notesFiles" :key="i" :class="['attach-item', f.type]">
                  <span class="attach-type">{{ f.type==='image'?'🖼️':f.type==='video'?'🎬':'🎙️' }}</span>
                  <span class="attach-name">{{ f.name }}</span>
                  <span class="attach-size">{{ f.size }}</span>
                </div>
              </div>
            </div>
          </div>

          <div v-if="detailTab==='attraction'&&attrName">
            <div v-if="attrLoading" class="attr-loading">
              <div class="think-seal">行</div>
              <div class="think-dots"><span></span><span></span><span></span></div>
              <p class="think-text">行知正在思考中...</p>
            </div>
            <div v-else class="attr-detail-wrap">
              <div class="attr-hero-card">
                <div v-if="attrImage" class="attr-hero-media">
                  <img :src="attrImage" :alt="attrName" class="attr-hero-img" @click="previewImage=attrImage;previewVisible=true" />
                </div>
                <div v-else class="attr-hero-empty">暂未获取到景点图片</div>
                <div class="attr-hero-main">
                  <div class="attr-hero-head">
                    <div>
                      <h3>{{ attrName }}</h3>
                      <p>{{ attrCity || detailTrip?.city || '旅行记录' }}</p>
                    </div>
                    <span v-if="attrSource" class="attr-source">{{ attrSource }}</span>
                  </div>
                  <div v-if="attrMeta.address || attrMeta.type || attrMeta.weather || attrMeta.tel || attrMeta.openTime || attrMeta.locationText" class="attr-meta-grid">
                    <div v-if="attrMeta.address" class="attr-meta-item"><span class="attr-meta-label">地址</span><span class="attr-meta-value">{{ attrMeta.address }}</span></div>
                    <div v-if="attrMeta.type" class="attr-meta-item"><span class="attr-meta-label">类型</span><span class="attr-meta-value">{{ attrMeta.type }}</span></div>
                    <div v-if="attrMeta.weather" class="attr-meta-item"><span class="attr-meta-label">天气</span><span class="attr-meta-value">{{ attrMeta.weather }}</span></div>
                    <div v-if="attrMeta.tel" class="attr-meta-item"><span class="attr-meta-label">电话</span><span class="attr-meta-value">{{ attrMeta.tel }}</span></div>
                    <div v-if="attrMeta.openTime" class="attr-meta-item"><span class="attr-meta-label">开放时间</span><span class="attr-meta-value">{{ attrMeta.openTime }}</span></div>
                    <div v-if="attrMeta.locationText" class="attr-meta-item"><span class="attr-meta-label">坐标</span><span class="attr-meta-value">{{ attrMeta.locationText }}</span></div>
                  </div>
                  <div v-if="attrMeta.lat !== null && attrMeta.lng !== null" class="attr-map-row">
                    <button class="attr-map-btn" @click="openAttractionMap">📍 在地图中打开这个景点</button>
                  </div>
                  <div class="attr-quick-actions">
                    <div class="attr-action-card">
                      <span class="attr-action-label">用这个景点新建旅行记录</span>
                      <input v-model="quickCreateDate" type="date" class="attr-action-input" />
                      <button class="attr-action-btn primary" :disabled="tripActionLoading" @click="createTripFromCurrentAttraction">
                        {{ tripActionLoading ? '创建中...' : '＋ 新建旅行记录' }}
                      </button>
                    </div>
                    <div class="attr-action-card">
                      <span class="attr-action-label">加入已有行程</span>
                      <select v-model="selectedTripId" class="attr-action-select">
                        <option value="">请选择一个旅行记录</option>
                        <option v-for="trip in tripOptions" :key="trip.id" :value="trip.id">
                          {{ trip.title || `${trip.start_date} ${trip.city}` }}
                          <template v-if="isSameTrip(trip.id)">（当前正在查看）</template>
                        </option>
                      </select>
                      <select v-model="selectedTripDayIndex" class="attr-action-select" :disabled="!selectedTripId || !selectedTripDayOptions.length">
                        <option v-if="!selectedTripDayOptions.length" :value="0">默认加入第1天</option>
                        <option v-for="day in selectedTripDayOptions" :key="day.value" :value="day.value">
                          {{ day.label }}
                        </option>
                      </select>
                      <button class="attr-action-btn" :disabled="tripActionLoading || !selectedTripId" @click="addCurrentAttractionToTrip">
                        {{ tripActionLoading ? '加入中...' : '加入这个行程' }}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              <div v-if="attrIntro" class="attr-intro" v-html="renderMd(attrIntro)"></div>
              <div v-else class="attr-empty-intro">暂时还没有拿到这处景点的详细介绍。</div>
            </div>
          </div>
        </div>
      </template>
    </div>

    <a-modal v-model:open="notesVisible" width="720px" :footer="null" @cancel="notesVisible=false" :bodyStyle="{padding:0}" wrapClassName="memo-modal">
      <div v-if="detailTrip" class="memo-wrap">
        <div class="memo-head">
          <div class="memo-head-icon">📝</div>
          <div class="memo-head-text">
            <h3>{{ detailTrip.title || detailTrip.start_date + ' ' + detailTrip.city }}</h3>
            <span>旅行笔记 · 记录此刻心情</span>
          </div>
        </div>
        <textarea v-model="notesText" class="memo-area" placeholder="写下你的旅行感悟...&#10;&#10;这里的风景让我想起...&#10;今天遇到了一件有趣的事...&#10;不知下次再来会是何时..."></textarea>
        <div class="memo-attach">
          <span class="attach-label">📎 附件</span>
          <div class="attach-list">
            <div v-for="(f,i) in notesFiles" :key="i" :class="['attach-item', f.type]">
              <span class="attach-type">{{ f.type==='image'?'🖼️':f.type==='video'?'🎬':'🎙️' }}</span>
              <span class="attach-name">{{ f.name }}</span>
              <span class="attach-size">{{ f.size }}</span>
              <span class="attach-del" @click="notesFiles.splice(i,1)">✕</span>
            </div>
          </div>
          <div class="attach-btns">
            <label class="attach-btn"><input type="file" accept="image/*" @change="e=>addFile(e,'image')" hidden />🖼️ 图片</label>
            <label class="attach-btn"><input type="file" accept="video/*" @change="e=>addFile(e,'video')" hidden />🎬 视频</label>
            <button class="attach-btn" @click="toggleRecord" :class="{recording:isRecording}">{{ isRecording ? '🔴 录音中' : '🎙️ 语音' }}</button>
          </div>
        </div>
        <div class="memo-foot">
          <span class="memo-hint">✍️ 所思所感，皆可落笔</span>
          <button class="memo-save" @click="saveNotes" :disabled="notesSaving">{{ notesSaving ? '保存中...' : '💾 保存笔记' }}</button>
        </div>
      </div>
      <div class="detail-ai" v-if="detailTrip" @click="fetchTripSuggestion">
        <div class="detail-ai-bubble" v-if="tripSuggestion">{{ tripSuggestion }}</div>
        <div class="detail-ai-btn"><span>🤖</span></div>
      </div>
    </a-modal>

    <a-modal v-model:open="previewVisible" :footer="null" width="80vw" @cancel="previewVisible = false">
      <img :src="previewImage" style="width:100%; max-height:80vh; object-fit:contain;" />
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  getHistory,
  getHistoryDetail,
  updateHistory,
  updateTripTasks,
  syncTripToPlaza,
  getAttractionDetail,
  getTripSuggestion,
  addAttractionToTrip,
  createTripWithAttraction,
  buildCurrentTripContext,
  getCurrentTripContext,
  setCurrentTripContext,
  setCurrentTripDetailTab,
  markCurrentTripViewed,
} from '@/services/api'
import { message } from 'ant-design-vue'

interface BudgetTypeSummary {
  label: string
  planned: number
  actual: number
  count: number
}

interface BudgetSummary {
  total_planned: number
  total_actual: number
  difference: number
  is_over_budget: boolean
  by_type?: Record<string, BudgetTypeSummary>
}

interface PrepChecklistItem {
  id: string
  category: string
  name: string
  done: boolean
}

interface AttractionQuickPayload {
  name: string
  city?: string
  intro?: string
  image?: string
  location?: { lat?: number | null; lng?: number | null } | null
}

interface AttractionMetaInfo {
  address: string
  type: string
  tel: string
  weather: string
  openTime: string
  locationText: string
  lat: number | null
  lng: number | null
}

interface TripDayOption {
  value: number
  label: string
}

interface TripActionFeedback {
  type: 'create' | 'add' | 'duplicate'
  title: string
  description: string
  tripId: string
}

interface TripSummary {
  id: string
  city: string
  start_date: string
  title: string
}

const PREP_CATEGORY_OPTIONS = ['证件', '衣物', '电子设备', '洗护', '药品', '其他']
const DEFAULT_PREP_ITEMS = [
  { category: '证件', name: '身份证/护照' },
  { category: '证件', name: '车票/机票信息' },
  { category: '衣物', name: '换洗衣物' },
  { category: '电子设备', name: '手机充电器' },
  { category: '电子设备', name: '充电宝' },
  { category: '洗护', name: '洗漱用品' },
]

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const detailTab = ref('itinerary')
const detailTrip = ref<any>(null)
const detailTasks = ref<any[]>([])
const prepChecklist = ref<PrepChecklistItem[]>([])
const previewVisible = ref(false)
const previewImage = ref('')
const tripSuggestion = ref('')
const tripSugLoading = ref(false)
const taskSaveState = ref<'idle' | 'saving' | 'saved' | 'error'>('idle')
const prepSaveState = ref<'idle' | 'saving' | 'saved' | 'error'>('idle')
const quickCreateDate = ref('')
const selectedTripId = ref('')
const selectedTripDayIndex = ref(0)
const tripActionLoading = ref(false)
const tripOptions = ref<TripSummary[]>([])
const selectedTripDayOptions = ref<TripDayOption[]>([])
const attrImage = ref('')
const attrCity = ref('')
const attrSource = ref('')
const attrName = ref('')
const attrIntro = ref('')
const attrLoading = ref(false)
const attrMeta = ref<AttractionMetaInfo>({
  address: '',
  type: '',
  tel: '',
  weather: '',
  openTime: '',
  locationText: '',
  lat: null,
  lng: null,
})
const tripActionFeedback = ref<TripActionFeedback | null>(null)
const currentAttractionPayload = ref<AttractionQuickPayload | null>(null)
const notesVisible = ref(false)
const notesText = ref('')
const notesSaving = ref(false)
const notesFiles = ref<any[]>([])
const isRecording = ref(false)
const prepCollapsed = ref<string[]>([])
const publishing = ref(false)
const published = ref(false)
const dragIdx = ref(-1)
const currentTripContext = ref(getCurrentTripContext())
const todayTripIndex = ref(0)
const tripInfoSaving = ref(false)
const tripInfoDraft = ref({ hotel: '', transport: '', tickets: '', contact: '', meetingPoint: '' })

let mediaRecorder: any = null
let audioChunks: any[] = []
let saveTimer: any = null
let prepSaveTimer: any = null
let taskSavedTimer: any = null
let prepSavedTimer: any = null

const detailTitle = computed(() => detailTrip.value ? (detailTrip.value.title || `${detailTrip.value.start_date} ${detailTrip.value.city}`) : '')
const taskDoneCnt = computed(() => detailTasks.value.filter(t => t.done).length)
const taskPct = computed(() => detailTasks.value.length ? Math.round(taskDoneCnt.value / detailTasks.value.length * 100) : 0)
const checklistDoneCnt = computed(() => prepChecklist.value.filter(item => item.done).length)
const checklistPct = computed(() => prepChecklist.value.length ? Math.round(checklistDoneCnt.value / prepChecklist.value.length * 100) : 0)
const attractionCount = computed(() => (detailTrip.value?.data?.days || []).reduce((sum: number, day: any) => sum + (day?.attractions?.length || 0), 0))
const groupedPrepChecklist = computed(() => PREP_CATEGORY_OPTIONS
  .map(category => {
    const items = prepChecklist.value.filter(item => item.category === category)
    const done = items.filter(item => item.done).length
    return {
      category,
      items,
      done,
      progress: items.length ? Math.round(done / items.length * 100) : 0,
    }
  })
  .filter(group => group.items.length > 0))
const detailBudget = computed<BudgetSummary>(() => detailTrip.value?.budget_summary || {
  total_planned: 0,
  total_actual: 0,
  difference: 0,
  is_over_budget: false,
  by_type: {},
})
const budgetTypeCards = computed(() => {
  const source = detailBudget.value.by_type || {}
  return [
    { key: 'attraction', icon: '🎯', ...(source.attraction || { label: '景点', planned: 0, actual: 0, count: 0 }) },
    { key: 'meal', icon: '🍽️', ...(source.meal || { label: '餐饮', planned: 0, actual: 0, count: 0 }) },
    { key: 'hotel', icon: '🏨', ...(source.hotel || { label: '酒店', planned: 0, actual: 0, count: 0 }) },
    { key: 'other', icon: '🧾', ...(source.other || { label: '其他', planned: 0, actual: 0, count: 0 }) },
  ]
})
const budgetInsightText = computed(() => {
  if (!detailTasks.value.length) return '还没有预算项目，先去“行程手札”里添加支出项吧。'
  if (!detailBudget.value.total_planned && !detailBudget.value.total_actual) return '你已经建好了项目，但还没开始填写预算金额。'
  if (detailBudget.value.is_over_budget) return `当前已超预算 ${formatMoney(Math.abs(detailBudget.value.difference || 0))}，建议优先压缩弹性支出。`
  if (!detailBudget.value.total_planned && detailBudget.value.total_actual > 0) return '你已经记录了实际花费，但还没填写计划预算，建议补全后更容易对比。'
  if (detailBudget.value.difference === 0) return '当前实际花费与计划预算持平，控制得刚刚好。'
  return `当前仍有 ${formatMoney(Math.abs(detailBudget.value.difference || 0))} 预算余量，可以继续按计划推进。`
})
const budgetHighlight = computed(() => {
  if (!budgetTypeCards.value.length || !detailTasks.value.length) return null
  const overs = budgetTypeCards.value
    .map(item => ({ ...item, diff: item.actual - item.planned }))
    .filter(item => item.diff > 0)
    .sort((a, b) => b.diff - a.diff)
  if (overs.length) {
    const top = overs[0]
    return {
      kind: 'over',
      title: `超支最多的是「${top.label}」`,
      description: `当前比计划多花了 ${formatMoney(top.diff)}，建议先从这一类支出里找可压缩项。`,
    }
  }
  const highest = budgetTypeCards.value
    .map(item => ({ ...item, total: item.actual || item.planned }))
    .filter(item => item.total > 0)
    .sort((a, b) => b.total - a.total)[0]
  if (!highest) return null
  return {
    kind: 'tip',
    title: `当前支出重点在「${highest.label}」`,
    description: `这一类目前累计 ${formatMoney(highest.actual || highest.planned)}，适合重点关注。`,
  }
})
const activeTabMeta = computed(() => {
  const map: Record<string, { title: string; description: string }> = {
    today: {
      title: '今日行程',
      description: todayPanelDescription.value,
    },
    itinerary: {
      title: '行程概览',
      description: `按天查看这次旅程的安排、景点与餐饮信息，目前共 ${detailTrip.value?.data?.days?.length || 0} 天。`,
    },
    tasks: {
      title: '行程手札',
      description: `这里集中维护任务、预算条目与完成进度，当前已完成 ${taskDoneCnt.value}/${detailTasks.value.length || 0}。`,
    },
    budget: {
      title: '预算',
      description: budgetInsightText.value,
    },
    prep: {
      title: '出发前清单',
      description: prepChecklist.value.length
        ? `当前共有 ${prepChecklist.value.length} 项待整理，已完成 ${checklistDoneCnt.value} 项。`
        : '先补齐证件、衣物和设备等出发前准备事项。',
    },
    notes: {
      title: '旅行笔记',
      description: notesFiles.value.length
        ? `这次旅程已经沉淀了 ${notesFiles.value.length} 份附件，可以继续补充文字与记录。`
        : '把旅途中的感受、图片和录音统一收在这里。',
    },
    attraction: {
      title: attrName.value || '景点详情',
      description: attrName.value
        ? '这里展示当前景点的图片、介绍、地图信息以及加入行程的快捷操作。'
        : '打开任一景点后，这里会展示对应的详情内容。',
    },
  }
  return map[detailTab.value] || map.itinerary
})
const tabShortcutCards = computed(() => {
  const tabs = [
    { key: 'tasks', icon: '📜', title: '手札', value: `${taskPct.value}%`, hint: `${taskDoneCnt.value}/${detailTasks.value.length || 0} 已完成` },
    { key: 'budget', icon: '💰', title: '预算', value: formatMoney(detailBudget.value.total_actual), hint: detailBudget.value.is_over_budget ? '当前超支中' : '实际已记录花费' },
    { key: 'prep', icon: '🧳', title: '清单', value: `${checklistPct.value}%`, hint: `${checklistDoneCnt.value}/${prepChecklist.value.length || 0} 已完成` },
    { key: 'notes', icon: '📝', title: '笔记', value: `${notesFiles.value.length} 份`, hint: detailTrip.value?.notes ? '已有文字记录' : '可继续补充内容' },
  ]
  return tabs.filter(item => item.key !== detailTab.value)
})
const taskSaveText = computed(() => taskSaveState.value === 'saving'
  ? '正在保存预算改动...'
  : taskSaveState.value === 'saved'
    ? '预算修改已自动保存'
    : taskSaveState.value === 'error'
      ? '预算保存失败，请稍后重试'
      : '改动会自动保存')
const prepSaveText = computed(() => prepSaveState.value === 'saving'
  ? '正在保存清单...'
  : prepSaveState.value === 'saved'
    ? '清单修改已自动保存'
    : prepSaveState.value === 'error'
      ? '清单保存失败，请稍后重试'
      : '勾选和编辑会自动保存')
const dayOptions = computed(() => (detailTrip.value?.data?.days || []).map((day: any, index: number) => ({
  index,
  label: day?.date ? `第${index + 1}天 · ${day.date}` : `第${index + 1}天`,
})))
const todayDayData = computed(() => {
  const days = detailTrip.value?.data?.days || []
  if (!days.length) return null
  return days[Math.min(Math.max(todayTripIndex.value, 0), days.length - 1)] || null
})
const todayDayShortLabel = computed(() => todayDayData.value ? `第${Number(todayDayData.value.day_index ?? todayTripIndex.value) + 1}天` : '今天')
const todayDayLabel = computed(() => dayOptions.value[todayTripIndex.value]?.label || todayDayShortLabel.value)
const todayTasks = computed(() => detailTasks.value.filter(task => String(task?.day || '').trim() === todayDayShortLabel.value))
const todayDoneCount = computed(() => todayTasks.value.filter(task => task.done).length)
const todayRemainingCount = computed(() => Math.max(0, todayTasks.value.length - todayDoneCount.value))
const todayPlannedCost = computed(() => todayTasks.value.reduce((sum, task) => sum + Number(task?.planned_cost || 0), 0))
const todayActualCost = computed(() => todayTasks.value.reduce((sum, task) => sum + Number(task?.actual_cost || 0), 0))
const todayAttractions = computed(() => todayDayData.value?.attractions || [])
const todayAttractionNames = computed(() => todayAttractions.value.map((item: any) => item?.name).filter(Boolean))
const todayPanelDescription = computed(() => todayTasks.value.length
  ? `今天这一天已经拆成 ${todayTasks.value.length} 条可执行任务，你可以直接勾选完成、登记花费，或跳去预算继续调整。`
  : '今天先从景点安排、预算和清单三条线里挑一条推进，后续会自动沉淀到这趟旅程里。')
const todayBudgetHint = computed(() => {
  if (!todayTasks.value.length) return '今天还没有独立预算项目，先去手札里补充。'
  if (todayActualCost.value > todayPlannedCost.value && todayPlannedCost.value > 0) return `今天已超出 ${formatMoney(todayActualCost.value - todayPlannedCost.value)}`
  if (!todayPlannedCost.value && todayActualCost.value > 0) return '今天已经记了实际花费，建议补上计划预算。'
  if (todayPlannedCost.value === todayActualCost.value) return '今天的预算和实际刚好持平。'
  return `今天还剩 ${formatMoney(Math.max(0, todayPlannedCost.value - todayActualCost.value))} 预算余量`
})
const currentTripStatusTitle = computed(() => {
  if (!detailTrip.value?.id) return '旅程详情'
  return currentTripContext.value?.tripId === detailTrip.value.id ? '这就是你当前正在推进的旅程' : '你可以把这条记录设为当前旅程'
})
const currentTripStatusDesc = computed(() => {
  if (!detailTrip.value?.id) return '当前旅程会在首页和历史列表中优先续接。'
  if (currentTripContext.value?.tripId === detailTrip.value.id) {
    return currentTripContext.value?.lastDetailTab
      ? `最近一次停留在「${currentTripContext.value.lastDetailTab}」，首页会直接帮你续回这条旅程。`
      : '首页和历史页都会把这条记录当作当前旅程继续续接。'
  }
  return '设为当前旅程后，首页会出现“继续当前旅程”入口，历史页也会优先回到这里。'
})
const tripInfoHintText = computed(() => {
  const filled = Object.values(tripInfoDraft.value).filter(value => String(value || '').trim()).length
  return filled ? `已填写 ${filled}/5 项旅程关键信息，保存后会跟随这条旅行记录一起保留。` : '这些信息会和任务、预算、清单、笔记一起沉淀在这条旅程记录中。'
})

function formatMoney(value: number) { return `¥${Number(value || 0).toLocaleString('zh-CN')}` }
function syncCurrentTripState() {
  currentTripContext.value = getCurrentTripContext()
}
function buildTripInfoFromTrip(trip: any) {
  const info = trip?.trip_info || {}
  return {
    hotel: String(info.hotel || '').trim(),
    transport: String(info.transport || '').trim(),
    tickets: String(info.tickets || '').trim(),
    contact: String(info.contact || '').trim(),
    meetingPoint: String(info.meetingPoint || '').trim(),
  }
}
function syncTripInfoDraftFromDetail() {
  tripInfoDraft.value = buildTripInfoFromTrip(detailTrip.value)
}
function syncCurrentTripContextForDetail(lastView = 'history') {
  if (!detailTrip.value?.id) return
  setCurrentTripContext(buildCurrentTripContext({
    tripId: detailTrip.value.id,
    title: detailTitle.value,
    city: detailTrip.value.city,
    startDate: detailTrip.value.start_date,
    source: 'history-select',
    lastView,
    lastDetailTab: detailTab.value,
  }))
  syncCurrentTripState()
}
function setTripAsCurrent() {
  if (!detailTrip.value?.id) return
  syncCurrentTripContextForDetail('history')
  message.success('已设为当前旅程')
}
function switchTodayDay(nextIndex: number) {
  const total = dayOptions.value.length
  if (!total) return
  todayTripIndex.value = Math.min(Math.max(nextIndex, 0), total - 1)
}
function focusTaskBudget(task: any) {
  detailTab.value = 'tasks'
  message.info(`可以直接修改「${task?.name || '这项任务'}」的实际花费`)
}
function getTripRecapAttractionName() {
  if (attrName.value) return attrName.value
  if (todayAttractionNames.value.length) return todayAttractionNames.value[0]
  const firstAttraction = (detailTrip.value?.data?.days || [])
    .flatMap((day: any) => day?.attractions || [])
    .map((item: any) => String(item?.name || '').trim())
    .find(Boolean)
  return firstAttraction || ''
}
function openTripRecapVideo() {
  if (!detailTrip.value?.id) return
  const attraction = getTripRecapAttractionName()
  syncCurrentTripContextForDetail('video')
  markCurrentTripViewed('video')
  router.push({
    path: '/dashboard',
    query: {
      view: 'video',
      tripId: detailTrip.value.id,
      tripTitle: detailTitle.value,
      tripCity: detailTrip.value.city || '',
      attraction: attraction || undefined,
    },
  })
}
async function copyShareSummary() {
  if (!detailTrip.value) return
  const recapAttraction = getTripRecapAttractionName()
  const lines = [
    `【${detailTitle.value}】`,
    `城市：${detailTrip.value.city || '待补充'}`,
    `日期：${detailTrip.value.start_date || '待补充'}`,
    `当前查看：${activeTabMeta.value.title}`,
    `今日重点：${todayAttractionNames.value.length ? todayAttractionNames.value.join('、') : '继续推进当前旅程'}`,
    `手札进度：${taskDoneCnt.value}/${detailTasks.value.length || 0}（${taskPct.value}%）`,
    `预算：计划 ${formatMoney(detailBudget.value.total_planned)} / 实际 ${formatMoney(detailBudget.value.total_actual)}`,
    `出发前清单：${checklistDoneCnt.value}/${prepChecklist.value.length || 0}`,
    recapAttraction ? `回顾视频：可从「生成回顾视频」继续制作（景点：${recapAttraction}）` : '回顾视频：可从「生成回顾视频」继续制作',
    tripInfoDraft.value.hotel ? `住宿：${tripInfoDraft.value.hotel}` : '',
    tripInfoDraft.value.transport ? `交通：${tripInfoDraft.value.transport}` : '',
    tripInfoDraft.value.tickets ? `票务：${tripInfoDraft.value.tickets}` : '',
    tripInfoDraft.value.contact ? `联系人：${tripInfoDraft.value.contact}` : '',
    tripInfoDraft.value.meetingPoint ? `提醒：${tripInfoDraft.value.meetingPoint}` : '',
  ].filter(Boolean)
  const payload = lines.join('\n')
  try {
    await navigator.clipboard.writeText(payload)
    message.success('旅程摘要已复制')
  } catch {
    message.warning('复制失败，请检查浏览器权限')
  }
}
async function saveTripInfo() {
  if (!detailTrip.value?.id) return
  tripInfoSaving.value = true
  try {
    const res = await updateHistory(detailTrip.value.id, { trip_info: { ...tripInfoDraft.value } })
    if (res?.data) {
      detailTrip.value = res.data
      syncTripInfoDraftFromDetail()
      syncCurrentTripContextForDetail('history')
    }
    message.success('旅程信息已保存')
  } catch {
    message.error('保存旅程信息失败')
  } finally {
    tripInfoSaving.value = false
  }
}
function budgetUsageWidth(planned: number, actual: number) {
  const base = planned > 0 ? planned : Math.max(actual, 1)
  return `${Math.min(100, Math.round((actual / base) * 100))}%`
}
function budgetUsageLabel(planned: number, actual: number) {
  if (!planned && !actual) return '尚未填写金额'
  if (!planned && actual > 0) return '仅记录了实际花费'
  if (actual > planned) return `超出 ${formatMoney(actual - planned)}`
  if (actual === planned) return '刚好用满预算'
  return `剩余 ${formatMoney(planned - actual)}`
}
function prepCategoryEmoji(category: string) {
  return category === '证件' ? '🪪'
    : category === '衣物' ? '👕'
      : category === '电子设备' ? '🔌'
        : category === '洗护' ? '🪥'
          : category === '药品' ? '💊'
            : '🧩'
}
function typeIcon(t: string) { return t==='attraction'?'🎯':t==='meal'?'🍽️':t==='hotel'?'🏨':'🧾' }
function toggleTask(t: any) { t.done=!t.done; autoSave() }
function updPlannedCost(t: any, v: string) { const n=parseInt(v); if(!isNaN(n)&&n>=0) t.planned_cost=n }
function updCost(t: any, v: string) { const n=parseInt(v); if(!isNaN(n)&&n>=0) t.actual_cost=n }
function cycleType(t: any) { const order=['attraction','meal','hotel','other']; const i=order.indexOf(t.type); t.type=order[(i+1+order.length)%order.length]; autoSave() }
function addTask() { detailTasks.value.push({id:Math.random().toString(36).slice(2,10),type:'attraction',day:'',name:'新项目',done:false,planned_cost:0,actual_cost:0}); autoSave() }
function togglePrepItem(item: PrepChecklistItem) { item.done = !item.done; autoSavePrep() }
function addPrepItem() {
  prepChecklist.value.push({ id: Math.random().toString(36).slice(2, 10), category: '其他', name: '待准备事项', done: false })
  autoSavePrep()
}
function removePrepItem(id: string) {
  prepChecklist.value = prepChecklist.value.filter(item => item.id !== id)
  autoSavePrep()
}
function addDefaultPrepItems() {
  const existed = new Set(prepChecklist.value.map(item => `${item.category}::${item.name}`))
  const nextItems = DEFAULT_PREP_ITEMS
    .filter(item => !existed.has(`${item.category}::${item.name}`))
    .map(item => ({ id: Math.random().toString(36).slice(2, 10), category: item.category, name: item.name, done: false }))
  if (!nextItems.length) { message.info('常用清单已经都在这里了'); return }
  prepChecklist.value.push(...nextItems)
  autoSavePrep()
}
function isPrepGroupCollapsed(category: string) {
  return prepCollapsed.value.includes(category)
}
function togglePrepGroup(category: string) {
  prepCollapsed.value = isPrepGroupCollapsed(category)
    ? prepCollapsed.value.filter(item => item !== category)
    : [...prepCollapsed.value, category]
}
function dropTask(toIdx: number) {
  if(dragIdx.value<0||dragIdx.value===toIdx)return
  const item = detailTasks.value.splice(dragIdx.value,1)[0]
  detailTasks.value.splice(toIdx,0,item)
  dragIdx.value=-1
  autoSave()
}

async function loadTripOptions() {
  try {
    const historyRes = await getHistory()
    tripOptions.value = historyRes.data || []
  } catch {
    tripOptions.value = []
  }
}

async function loadDetail(id = String(route.params.id || '')) {
  if (!id) { detailTrip.value = null; loading.value = false; return }
  loading.value = true
  try {
    const [res] = await Promise.all([getHistoryDetail(id), loadTripOptions()])
    detailTrip.value = res.data
    const latestCurrentTrip = getCurrentTripContext()
    const rememberedTab = latestCurrentTrip?.tripId === res.data?.id
      ? String(latestCurrentTrip?.lastDetailTab || '').trim()
      : ''
    if (rememberedTab) detailTab.value = rememberedTab
    detailTasks.value = [...(res.data.tasks || [])]
    prepChecklist.value = [...(res.data.prep_checklist || [])]
    notesText.value = res.data.notes || ''
    notesFiles.value = [...(res.data.files || [])]
    published.value = false
    tripSuggestion.value = ''
    tripActionFeedback.value = null
    attrName.value = ''
    attrIntro.value = ''
    attrImage.value = ''
    attrCity.value = ''
    attrSource.value = ''
    currentAttractionPayload.value = null
    prepCollapsed.value = []
    syncTripInfoDraftFromDetail()
    syncCurrentTripContextForDetail('history')
    syncCurrentTripState()
    todayTripIndex.value = Math.min(Math.max((res.data?.data?.days || []).findIndex((day: any) => day?.date === new Date().toISOString().slice(0, 10)), 0), Math.max((res.data?.data?.days || []).length - 1, 0))
    resetAttractionMeta()
    if (!quickCreateDate.value) quickCreateDate.value = detailTrip.value?.start_date || new Date().toISOString().slice(0, 10)
    fetchTripSuggestion()
  } catch {
    detailTrip.value = null
    message.error('获取详情失败')
  } finally {
    loading.value = false
  }
}

function goBackToHistory() {
  markCurrentTripViewed('history')
  router.push({ path: '/dashboard', query: { view: 'history' } })
}

function openTripDetail(id: string) {
  if (!id) return
  router.push({ path: `/history/${id}` })
}

function resetAttractionMeta() {
  attrMeta.value = { address: '', type: '', tel: '', weather: '', openTime: '', locationText: '', lat: null, lng: null }
}
function resetTripActionFeedback() { tripActionFeedback.value = null }
function buildAttractionMeta(detail: any, fallbackAttraction?: any): AttractionMetaInfo {
  const geo = detail?.geo || {}
  const rawLocation = String(geo.location || '').trim()
  let lat: number | null = null
  let lng: number | null = null
  if (rawLocation.includes(',')) {
    const [rawLng, rawLat] = rawLocation.split(',')
    const parsedLat = Number(rawLat)
    const parsedLng = Number(rawLng)
    if (Number.isFinite(parsedLat) && Number.isFinite(parsedLng)) { lat = parsedLat; lng = parsedLng }
  }
  if (lat === null || lng === null) {
    const fallbackLocation = fallbackAttraction?.location || {}
    const fallbackLat = fallbackLocation.latitude ?? fallbackLocation.lat ?? null
    const fallbackLng = fallbackLocation.longitude ?? fallbackLocation.lng ?? null
    lat = fallbackLat != null ? Number(fallbackLat) : null
    lng = fallbackLng != null ? Number(fallbackLng) : null
  }
  return {
    address: String(geo.address || fallbackAttraction?.location?.address || '').trim(),
    type: String(geo.type || '').trim(),
    tel: String(geo.tel || '').trim(),
    weather: String(detail?.weather || '').trim(),
    openTime: String(geo.opentime || geo.open_time || '').trim(),
    locationText: rawLocation,
    lat: Number.isFinite(lat) ? Number(lat) : null,
    lng: Number.isFinite(lng) ? Number(lng) : null,
  }
}
function openAttractionMap() {
  const { lat, lng } = attrMeta.value
  if (lat == null || lng == null) { message.info('暂时没有这处景点的坐标信息'); return }
  window.open(`https://uri.amap.com/marker?position=${lng},${lat}&name=${encodeURIComponent(attrName.value)}`, '_blank')
}
function isSameTrip(tripId: string) { return !!tripId && tripId === detailTrip.value?.id }
function normalizeAttractionPayload(name: string, city = '', fallbackAttraction?: any): AttractionQuickPayload {
  const fallbackLocation = fallbackAttraction?.location || {}
  const lat = fallbackLocation.latitude ?? fallbackLocation.lat ?? null
  const lng = fallbackLocation.longitude ?? fallbackLocation.lng ?? null
  return {
    name,
    city,
    intro: attrIntro.value || fallbackAttraction?.description || '',
    image: attrImage.value || fallbackAttraction?.image || '',
    location: lat != null && lng != null ? { lat: Number(lat), lng: Number(lng) } : null,
  }
}
async function createTripFromCurrentAttraction() {
  if (!currentAttractionPayload.value?.name) { message.warning('请先打开一个景点详情'); return }
  if (!quickCreateDate.value) { message.warning('请先选择出发日期'); return }
  tripActionLoading.value = true
  resetTripActionFeedback()
  try {
    const res = await createTripWithAttraction({
      city: currentAttractionPayload.value.city || detailTrip.value?.city || '未知城市',
      startDate: quickCreateDate.value,
      attraction: currentAttractionPayload.value,
    })
    if (res?.success) {
      const createdTrip = res?.data || null
      const newTripId = createdTrip?.id || ''
      const summary = createdTrip?.title || `${quickCreateDate.value} ${currentAttractionPayload.value.city || detailTrip.value?.city || '旅行记录'}`
      tripActionFeedback.value = {
        type: 'create',
        title: `已为「${currentAttractionPayload.value.name}」新建旅行记录`,
        description: `出发日期：${quickCreateDate.value}，已自动收进 ${summary}`,
        tripId: newTripId,
      }
      if (newTripId) {
        setCurrentTripContext(buildCurrentTripContext({
          tripId: newTripId,
          title: summary,
          city: currentAttractionPayload.value.city || detailTrip.value?.city || '',
          startDate: quickCreateDate.value,
          source: 'attraction-create',
          lastView: 'history',
        }))
        syncCurrentTripState()
      }
      message.success(res.message || '已新建旅行记录')
      await loadTripOptions()
      if (newTripId) openTripDetail(newTripId)
    } else {
      message.error(res?.message || '新建旅行记录失败')
    }
  } catch {
    message.error('新建旅行记录失败，请稍后再试')
  } finally {
    tripActionLoading.value = false
  }
}
async function addCurrentAttractionToTrip() {
  if (!currentAttractionPayload.value?.name) { message.warning('请先打开一个景点详情'); return }
  if (!selectedTripId.value) { message.warning('请先选择一个旅行记录'); return }
  tripActionLoading.value = true
  resetTripActionFeedback()
  try {
    const targetTripId = selectedTripId.value
    const targetTripLabel = tripOptions.value.find(item => item.id === targetTripId)?.title
      || tripOptions.value.find(item => item.id === targetTripId)?.start_date
      || '所选旅行记录'
    const dayLabel = selectedTripDayOptions.value.find(day => day.value === selectedTripDayIndex.value)?.label || '第1天'
    const beforeDetail = await getHistoryDetail(targetTripId)
    const beforeNames = new Set((beforeDetail?.data?.data?.days || []).flatMap((day: any) => day?.attractions || []).map((item: any) => String(item?.name || '').trim()).filter(Boolean))
    const res = await addAttractionToTrip({ tripId: targetTripId, dayIndex: selectedTripDayIndex.value, attraction: currentAttractionPayload.value })
    if (res?.success) {
      const alreadyExists = beforeNames.has(currentAttractionPayload.value.name)
      tripActionFeedback.value = alreadyExists
        ? { type: 'duplicate', title: `「${currentAttractionPayload.value.name}」已经在这个行程里了`, description: `我帮你直接打开了 ${targetTripLabel}，你可以继续调整第几天或补充其他景点。`, tripId: targetTripId }
        : { type: 'add', title: `已加入 ${targetTripLabel}`, description: `已放入 ${dayLabel}，现在就带你回到这条旅行记录继续查看。`, tripId: targetTripId }
      setCurrentTripContext(buildCurrentTripContext({
        tripId: targetTripId,
        title: tripOptions.value.find(item => item.id === targetTripId)?.title || targetTripLabel,
        city: tripOptions.value.find(item => item.id === targetTripId)?.city || currentAttractionPayload.value.city || '',
        startDate: tripOptions.value.find(item => item.id === targetTripId)?.start_date || '',
        source: 'attraction-add',
        lastView: 'history',
      }))
      syncCurrentTripState()
      if (alreadyExists) message.info('这个景点已经在行程里了，已为你打开对应记录')
      else message.success(res.message || '已加入行程')
      await loadTripOptions()
      openTripDetail(targetTripId)
    } else {
      message.error(res?.message || '加入行程失败')
    }
  } catch {
    message.error('加入行程失败，请稍后再试')
  } finally {
    tripActionLoading.value = false
  }
}
async function openAttractionPage(name: string, city = '', fallbackAttraction?: any) {
  attrName.value = name
  detailTab.value = 'attraction'
  attrLoading.value = true
  attrIntro.value = ''
  attrImage.value = ''
  attrCity.value = city || detailTrip.value?.city || ''
  attrSource.value = ''
  currentAttractionPayload.value = normalizeAttractionPayload(name, attrCity.value, fallbackAttraction)
  resetAttractionMeta()
  resetTripActionFeedback()
  if (!quickCreateDate.value) quickCreateDate.value = new Date().toISOString().slice(0, 10)
  try {
    const targetCity = city || detailTrip.value?.city || ''
    const d = await getAttractionDetail(name, targetCity)
    if (d.success) {
      const detail = d.data || {}
      attrIntro.value = detail.intro || '暂时还没有拿到这处景点的详细介绍。'
      attrImage.value = detail.image || fallbackAttraction?.image || ''
      attrCity.value = detail.city || targetCity
      attrSource.value = d.source ? `来源：${d.source}` : ''
      const nextMeta = buildAttractionMeta(detail, fallbackAttraction)
      attrMeta.value = nextMeta
      currentAttractionPayload.value = {
        name: detail.name || name,
        city: detail.city || targetCity,
        intro: detail.intro || fallbackAttraction?.description || '',
        image: detail.image || fallbackAttraction?.image || '',
        location: nextMeta.lat != null && nextMeta.lng != null ? { lat: nextMeta.lat, lng: nextMeta.lng } : normalizeAttractionPayload(name, targetCity, fallbackAttraction).location,
      }
    } else {
      attrIntro.value = '抱歉，获取景点介绍失败'
      attrImage.value = fallbackAttraction?.image || ''
      currentAttractionPayload.value = normalizeAttractionPayload(name, targetCity, fallbackAttraction)
    }
  } catch {
    attrIntro.value = '网络异常'
    attrImage.value = fallbackAttraction?.image || ''
    currentAttractionPayload.value = normalizeAttractionPayload(name, city || detailTrip.value?.city || '', fallbackAttraction)
  } finally {
    attrLoading.value = false
  }
}
function buildTripDayOptions(days: any[] = []) {
  if (!Array.isArray(days) || !days.length) { selectedTripDayOptions.value = [{ value: 0, label: '第1天' }]; selectedTripDayIndex.value = 0; return }
  selectedTripDayOptions.value = days.map((day: any, index: number) => ({ value: Number(day?.day_index ?? index), label: day?.date ? `第${index + 1}天 · ${day.date}` : `第${index + 1}天` }))
  const exists = selectedTripDayOptions.value.some(day => day.value === selectedTripDayIndex.value)
  if (!exists) selectedTripDayIndex.value = selectedTripDayOptions.value[0]?.value ?? 0
}
function renderMd(t: string): string {
  if (!t) return ''
  let h = t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
  h = h.replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')
  h = h.replace(/\*(.+?)\*/g,'<em>$1</em>')
  h = h.replace(/`(.+?)`/g,'<code>$1</code>')
  h = h.replace(/^### (.+)$/gm,'<h4>$1</h4>')
  h = h.replace(/^## (.+)$/gm,'<h3>$1</h3>')
  h = h.replace(/^# (.+)$/gm,'<h2>$1</h2>')
  h = h.replace(/^- (.+)$/gm,'<li>$1</li>')
  h = h.replace(/^\d+\. (.+)$/gm,'<li>$1</li>')
  h = h.replace(/\n\n/g,'<br><br>')
  h = h.replace(/\n/g,'<br>')
  return h
}
async function fetchTripSuggestion() {
  if (tripSugLoading.value || !detailTrip.value) return
  tripSugLoading.value = true
  try {
    const d = await getTripSuggestion(detailTrip.value.city)
    if (d.success) tripSuggestion.value = d.suggestion
  } catch { tripSuggestion.value = '出行记得注意天气变化哦～' }
  finally { tripSugLoading.value = false }
}
function addFile(e: Event, type: string) {
  const input = e.target as HTMLInputElement
  if (!input.files?.length) return
  const file = input.files[0]
  const maxSize = type === 'video' ? 15 * 1024 * 1024 : 5 * 1024 * 1024
  if (file.size > maxSize) { message.warning(`${type==='video'?'视频':'图片'}不能超过${type==='video'?15:5}MB`); return }
  const reader = new FileReader()
  reader.onload = () => notesFiles.value.push({ type, name: file.name, size: formatSize(file.size), data: reader.result as string })
  reader.readAsDataURL(file)
}
function formatSize(b: number) { return b<1024*1024 ? Math.round(b/1024)+'KB' : (b/(1024*1024)).toFixed(1)+'MB' }
async function toggleRecord() {
  if (isRecording.value) { mediaRecorder?.stop(); return }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    mediaRecorder = new MediaRecorder(stream)
    audioChunks = []
    mediaRecorder.ondataavailable = (e: any) => audioChunks.push(e.data)
    mediaRecorder.onstop = () => {
      stream.getTracks().forEach((t: any) => t.stop())
      const blob = new Blob(audioChunks, { type: 'audio/webm' })
      const reader = new FileReader()
      reader.onload = () => notesFiles.value.push({ type: 'audio', name: `录音_${new Date().toLocaleTimeString()}.webm`, size: formatSize(blob.size), data: reader.result as string })
      reader.readAsDataURL(blob)
      isRecording.value = false
    }
    mediaRecorder.start(); isRecording.value = true
  } catch { message.warning('无法访问麦克风') }
}
function openNotesEditor() {
  notesText.value = detailTrip.value?.notes || ''
  notesFiles.value = [...(detailTrip.value?.files || [])]
  notesVisible.value = true
}
async function saveNotes() {
  if (!detailTrip.value) return
  notesSaving.value = true
  try {
    const res = await updateHistory(detailTrip.value.id, { notes: notesText.value, files: notesFiles.value })
    if (res?.data) detailTrip.value = res.data
    message.success('笔记已保存')
    notesVisible.value = false
    notesFiles.value = [...(res?.data?.files || notesFiles.value)]
  } catch { message.error('保存失败') }
  finally { notesSaving.value = false }
}
async function autoSave() {
  clearTimeout(saveTimer)
  clearTimeout(taskSavedTimer)
  taskSaveState.value = 'saving'
  saveTimer=setTimeout(async()=>{
    if(!detailTrip.value)return
    try {
      const res = await updateTripTasks(detailTrip.value.id, detailTasks.value)
      detailTrip.value = res?.data || detailTrip.value
      detailTasks.value = [...(res?.data?.tasks || detailTasks.value)]
      taskSaveState.value = 'saved'
      taskSavedTimer = setTimeout(() => { taskSaveState.value = 'idle' }, 1600)
      await loadTripOptions()
    } catch {
      taskSaveState.value = 'error'
    }
  },800)
}
async function autoSavePrep() {
  clearTimeout(prepSaveTimer)
  clearTimeout(prepSavedTimer)
  prepSaveState.value = 'saving'
  prepSaveTimer=setTimeout(async()=>{
    if(!detailTrip.value?.id)return
    try {
      const res = await updateHistory(detailTrip.value.id, { prep_checklist: prepChecklist.value })
      if (res?.data) {
        detailTrip.value = res.data
        prepChecklist.value = [...(res.data.prep_checklist || prepChecklist.value)]
      }
      prepSaveState.value = 'saved'
      prepSavedTimer = setTimeout(() => { prepSaveState.value = 'idle' }, 1600)
      await loadTripOptions()
    } catch {
      prepSaveState.value = 'error'
    }
  },800)
}
async function publishToPlaza() {
  if(!detailTrip.value)return
  publishing.value=true
  try {
    const attractions = detailTasks.value.filter((t:any)=>t.type==='attraction').map((t:any)=>t.name)
    await syncTripToPlaza(detailTrip.value.city, attractions)
    published.value=true
    message.success('已同步到数据广场！')
  } catch { message.error('同步失败') }
  finally { publishing.value=false }
}

watch(selectedTripId, async (id) => {
  if (!id) { selectedTripDayOptions.value = []; selectedTripDayIndex.value = 0; return }
  try {
    const res = await getHistoryDetail(id)
    buildTripDayOptions(res?.data?.data?.days || [])
  } catch {
    selectedTripDayOptions.value = [{ value: 0, label: '第1天' }]
    selectedTripDayIndex.value = 0
  }
})
watch(detailTab, (tab) => {
  if (!tab) return
  setCurrentTripDetailTab(tab)
  syncCurrentTripContextForDetail('history')
})
watch(() => route.params.id, (id) => { loadDetail(String(id || '')) })

onMounted(() => {
  syncCurrentTripState()
  loadDetail()
  window.addEventListener('storage', syncCurrentTripState)
})

onBeforeUnmount(() => {
  window.removeEventListener('storage', syncCurrentTripState)
})
</script>

<style scoped>
.history-detail-page { min-height: 100%; background: linear-gradient(180deg, #faf7f2 0%, #fff 100%); }
.history-detail-shell { max-width: 1120px; margin: 0 auto; padding: 24px; animation: viewIn .35s ease-out both; }
@keyframes viewIn { from{opacity:0;transform:scale(.98) translateY(6px)} to{opacity:1;transform:scale(1) translateY(0)} }
.detail-hero-panel { margin-bottom: 18px; padding: 20px; border: 1px solid #eadccf; border-radius: 24px; background: linear-gradient(135deg, #fffaf6 0%, #fff 58%, #fdf4ee 100%); box-shadow: 0 16px 40px rgba(139,69,19,.06); }
.detail-page-topbar { display:flex; align-items:flex-start; gap:18px; margin-bottom:24px; }
.hero-topbar { margin-bottom: 20px; }
.detail-back-btn { flex-shrink:0; border:none; border-radius:14px; padding:12px 16px; background:#fff; color:#8b5a3c; border:1px solid #eadccf; cursor:pointer; font-size:14px; transition:all .18s; }
.detail-back-btn:hover { transform:translateY(-1px); box-shadow:0 6px 18px rgba(139,69,19,.08); }
.detail-page-heading { display:flex; flex-direction:column; gap:6px; }
.hero-heading { flex: 1; min-width: 0; }
.detail-heading-badges { display:flex; flex-wrap:wrap; gap:8px; margin-bottom: 4px; }
.heading-badge { display:inline-flex; align-items:center; padding:6px 10px; border-radius:999px; background:#fdf0e8; color:#c43b3b; font-size:12px; font-weight:600; }
.heading-badge.soft { background:#fff; color:#8b6b52; border:1px solid #f0dfd1; }
.detail-page-heading h1 { margin:0; font-size:30px; color:#5c3a21; font-family:'STKaiti','楷体','KaiTi',serif; }
.detail-page-heading p { margin:0; color:#b08a72; font-size:14px; }
.detail-hero-aside { min-width: 180px; padding: 14px 16px; border-radius: 18px; border: 1px solid #f0dfd1; background: rgba(255,255,255,.82); display:flex; flex-direction:column; gap:6px; box-shadow: inset 0 1px 0 rgba(255,255,255,.6); }
.hero-aside-label { font-size:12px; color:#b08a72; }
.detail-hero-aside strong { font-size:18px; color:#5c3a21; }
.detail-hero-aside p { margin:0; font-size:12px; line-height:1.7; color:#8b6b52; }
.detail-summary-grid { display:grid; grid-template-columns:repeat(4, minmax(0, 1fr)); gap:14px; margin-bottom:18px; }
.summary-stat-card { padding:18px; border-radius:18px; border:1px solid #eadccf; background:#fff; display:flex; flex-direction:column; gap:8px; box-shadow:0 8px 24px rgba(139,69,19,.04); }
.summary-stat-card span { font-size:13px; color:#8b6b52; }
.summary-stat-card strong { font-size:24px; color:#5c3a21; }
.summary-stat-card p { margin:0; font-size:12px; line-height:1.7; color:#b08a72; }
.summary-stat-card.progress { background:linear-gradient(180deg,#fffaf6 0%,#fff 100%); }
.summary-stat-card.budget.save, .summary-stat-card.prep { background:linear-gradient(180deg,#f9fff6 0%,#fff 100%); }
.summary-stat-card.budget.over { background:linear-gradient(180deg,#fff5f5 0%,#fff 100%); border-color:#ffccc7; }
.detail-overview-strip { display:grid; grid-template-columns:repeat(4, minmax(0, 1fr)); gap:12px; margin:0 0 18px; }
.overview-pill { padding:14px 16px; border-radius:16px; border:1px solid #f0dfd1; background:linear-gradient(180deg,#fffaf6 0%,#fff 100%); display:flex; flex-direction:column; gap:6px; }
.overview-pill span { font-size:12px; color:#b08a72; }
.overview-pill strong { font-size:16px; color:#5c3a21; line-height:1.5; }
.sticky-tabs { position:sticky; top:0; z-index:5; }
.detail-focus-panel { display:grid; grid-template-columns: minmax(0, 1.1fr) minmax(0, 1.4fr); gap:14px; margin-top:14px; padding:16px; border:1px solid #eadccf; border-radius:18px; background:linear-gradient(135deg,#fffaf6 0%,#fff 60%,#fdf4ee 100%); box-shadow:0 10px 24px rgba(139,69,19,.05); }
.detail-focus-main { display:flex; flex-direction:column; gap:8px; padding:2px 2px 2px 4px; }
.detail-focus-label { font-size:12px; color:#b08a72; letter-spacing:.08em; }
.detail-focus-main strong { font-size:22px; color:#5c3a21; font-family:'STKaiti','楷体','KaiTi',serif; }
.detail-focus-main p { margin:0; font-size:13px; line-height:1.9; color:#8b6b52; }
.detail-focus-shortcuts { display:grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap:10px; }
.detail-shortcut-card { border:1px solid #f0dfd1; border-radius:16px; background:#fff; padding:14px 14px 12px; text-align:left; cursor:pointer; display:flex; flex-direction:column; gap:6px; transition:all .18s; box-shadow:0 6px 18px rgba(139,69,19,.04); }
.detail-shortcut-card:hover { transform:translateY(-1px); border-color:#dcbba7; box-shadow:0 10px 22px rgba(139,69,19,.08); }
.detail-shortcut-card.active { border-color:#c43b3b; background:linear-gradient(180deg,#fff5f3 0%,#fff 100%); box-shadow:0 12px 22px rgba(196,59,59,.08); }
.detail-shortcut-top { font-size:12px; color:#b08a72; }
.detail-shortcut-card strong { font-size:20px; color:#5c3a21; line-height:1.3; }
.detail-shortcut-card p { margin:0; font-size:12px; line-height:1.7; color:#8b6b52; }
.detail-page-content { padding:22px 0 12px; }
.detail-missing-state { text-align:center; padding:80px 0; }
.page-loading { min-height:40vh; }
.notes-panel-head { display:flex; align-items:flex-start; justify-content:space-between; gap:12px; margin-bottom:14px; }
.notes-panel-head h4 { margin:0; font-size:16px; color:#5c3a21; font-family:'STKaiti','楷体','KaiTi',serif; }
.notes-panel-head p { margin:6px 0 0; font-size:13px; color:#b08a72; line-height:1.7; }
.notes-edit-btn { border:none; border-radius:12px; background:#fdf0e8; color:#c43b3b; padding:10px 14px; font-size:13px; cursor:pointer; transition:all .18s; }
.notes-edit-btn:hover { transform:translateY(-1px); box-shadow:0 6px 16px rgba(196,59,59,.1); }
.detail-files-section { margin-top:16px; }
.detail-files-section h4 { margin:0 0 10px; font-size:15px; color:#5c3a21; }
.page-attach-list { margin-top:6px; }

.detail-tabs { display:flex; gap:0; border-bottom:2px solid #eadccf; padding:0 24px; background:#faf7f2; border-radius:16px 16px 0 0; overflow:auto hidden; }
.dt-tab { padding:12px 20px; font-size:14px; color:#b8a088; cursor:pointer; border-bottom:2px solid transparent; margin-bottom:-2px; transition:all .2s; font-family:'STKaiti','楷体','KaiTi',serif; white-space:nowrap }
.dt-tab:hover { color:#5c3a21 }
.dt-tab.active { color:#c43b3b; border-bottom-color:#c43b3b; font-weight:600 }
.trip-action-feedback { display:flex; align-items:center; justify-content:space-between; gap:14px; margin:0 0 16px; padding:14px 16px; border-radius:14px; border:1px solid #eadccf; background:linear-gradient(180deg,#fffaf6 0%,#fff 100%); }
.trip-action-feedback.create { border-color:#d7c2f5; background:linear-gradient(180deg,#faf6ff 0%,#fff 100%); }
.trip-action-feedback.add { border-color:#cfe7d2; background:linear-gradient(180deg,#f7fff8 0%,#fff 100%); }
.trip-action-feedback.duplicate { border-color:#f3dfb3; background:linear-gradient(180deg,#fffaf0 0%,#fff 100%); }
.trip-action-feedback-main { display:flex; flex-direction:column; gap:4px; }
.trip-action-feedback-main strong { color:#5c3a21; font-size:15px; }
.trip-action-feedback-main p { margin:0; color:#8b6b52; font-size:13px; line-height:1.7; }
.trip-action-feedback-btn { flex-shrink:0; border:none; border-radius:12px; background:#c43b3b; color:#fff; padding:10px 14px; font-size:13px; cursor:pointer; transition:all .18s; }
.trip-action-feedback-btn:hover { transform:translateY(-1px); box-shadow:0 6px 16px rgba(196,59,59,.18); }
.trip-progress-bar { height:6px;background:#eadccf;border-radius:3px;margin-bottom:14px;overflow:hidden }
.trip-progress-fill, .task-progress-fill { height:100%;background:linear-gradient(90deg,#c43b3b,#52c41a);border-radius:3px;transition:width .4s }
.task-header { display:flex;align-items:center;justify-content:space-between;margin-bottom:8px }
.task-header h4 { margin:0;font-size:15px;color:#5c3a21;font-family:'STKaiti','楷体','KaiTi',serif }
.task-progress-text { font-size:13px;color:#b8a088 }
.task-progress-bar { height:6px;background:#eadccf;border-radius:3px;margin-bottom:14px;overflow:hidden }
.panel-save-hint { margin:-2px 0 14px; padding:8px 12px; border-radius:10px; font-size:12px; line-height:1.6; background:#fcf7f1; color:#8b6b52; border:1px solid #f0dfd1; transition:all .2s; }
.panel-save-hint.saving { background:#fff7e8; border-color:#f7d591; color:#ad6800; }
.panel-save-hint.saved { background:#f6ffed; border-color:#d9f7be; color:#389e0d; }
.panel-save-hint.error { background:#fff1f0; border-color:#ffccc7; color:#cf1322; }
.panel-empty-state { padding:18px 16px; border-radius:14px; border:1px dashed #e3d3c6; background:linear-gradient(180deg,#fffaf6 0%,#fff 100%); color:#8b6b52; display:flex; flex-direction:column; gap:6px; }
.panel-empty-state.compact { padding:16px 14px; }
.panel-empty-state strong { color:#5c3a21; font-size:15px; }
.panel-empty-state p { margin:0; font-size:13px; line-height:1.8; }
.task-list { display:flex;flex-direction:column;gap:4px;max-height:360px;overflow-y:auto }
.task-cost-head { display:grid; grid-template-columns: 44px minmax(0,1fr) 78px 78px; gap:8px; padding:0 34px 6px 92px; font-size:12px; color:#b8a088; }
.task-cost-head-day { text-align:center; }
.task-cost-head-name { text-align:left; }
.task-cost-head-price { text-align:right; }
.task-item { display:flex;align-items:center;gap:6px;padding:6px 8px;border-radius:8px;transition:background .15s }
.task-item:hover { background:#fdf8f3 }
.task-item.done { opacity:.6 }
.task-drag-handle { cursor:grab;color:#ccc;font-size:14px;flex-shrink:0;letter-spacing:-2px;user-select:none }
.task-drag-handle:active { cursor:grabbing }
.task-check { cursor:pointer;font-size:18px;flex-shrink:0;transition:transform .15s }
.task-check:hover { transform:scale(1.2) }
.task-type { font-size:14px;flex-shrink:0;cursor:pointer;transition:transform .15s }
.task-type:hover { transform:scale(1.15) }
.task-day-inp { width:44px;padding:3px 4px;border:1px solid transparent;border-radius:4px;font-size:11px;color:#b8a088;background:transparent;text-align:center;transition:border-color .2s }
.task-day-inp:focus { border-color:#c43b3b;background:#fff;outline:none }
.task-name-inp { flex:1;padding:3px 6px;border:1px solid transparent;border-radius:4px;font-size:13px;color:#5c3a21;background:transparent;min-width:0;transition:border-color .2s }
.task-name-inp:focus { border-color:#c43b3b;background:#fff;outline:none }
.task-name-inp.strike { text-decoration:line-through;color:#b8a088 }
.task-cost-wrap { display:flex; align-items:center; gap:2px; }
.task-cost-label { font-size:13px;color:#b8a088;flex-shrink:0 }
.task-cost { width:56px;padding:3px 4px;border:1px solid transparent;border-radius:4px;font-size:13px;text-align:right;background:transparent;color:#5c3a21;transition:border-color .2s }
.task-cost:focus { border-color:#c43b3b;background:#fff;outline:none }
.task-del { font-size:14px;color:#ccc;cursor:pointer;flex-shrink:0;padding:2px 4px;border-radius:4px;opacity:0;transition:all .15s }
.task-item:hover .task-del, .prep-item:hover .task-del { opacity:1 }
.task-del:hover { color:#c43b3b;background:#fde8e8 }
.task-add-row { padding:4px 0 }
.task-add-btn { padding:6px 14px;border:1px dashed #d4a89a;border-radius:12px;background:transparent;color:#b8a088;font-size:13px;cursor:pointer;transition:all .2s;width:100% }
.task-add-btn:hover { border-color:#c43b3b;color:#c43b3b;background:#fdf8f3 }
.task-publish-btn { margin-top:10px;padding:10px 20px;border:none;border-radius:16px;background:linear-gradient(135deg,#c43b3b,#a0522d);color:#fff;font-size:14px;cursor:pointer;font-family:'STKaiti','楷体','KaiTi',serif;transition:all .2s;animation:pulseGlow 2s infinite;width:100% }
.task-publish-btn:hover:not(:disabled) { transform:translateY(-1px);box-shadow:0 4px 16px rgba(196,59,59,.35) }
.task-publish-btn:disabled { opacity:.5;cursor:not-allowed;animation:none }
@keyframes pulseGlow { 0%,100%{box-shadow:0 0 0 0 rgba(196,59,59,.3)} 50%{box-shadow:0 0 0 8px rgba(196,59,59,0)} }
.task-publish-done { text-align:center;font-size:13px;color:#52c41a;margin-top:6px;font-family:'STKaiti','楷体','KaiTi',serif }
.budget-panel { display:flex; flex-direction:column; gap:16px; }
.budget-overview { display:grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap:12px; }
.budget-stat-card { padding:16px; border-radius:14px; background:#fff7e8; border:1px solid #f5d7a7; display:flex; flex-direction:column; gap:6px; }
.budget-stat-card.actual { background:#f0f5ff; border-color:#d6e4ff; }
.budget-stat-card.over { background:#fff1f0; border-color:#ffccc7; color:#cf1322; }
.budget-stat-card.save { background:#f6ffed; border-color:#d9f7be; color:#389e0d; }
.budget-stat-label { font-size:13px; color:inherit; opacity:.8; }
.budget-stat-card strong { font-size:22px; color:#5c3a21; }
.budget-stat-card.over strong, .budget-stat-card.save strong { color:inherit; }
.budget-summary-note { padding:12px 14px; border-radius:12px; background:#fcf7f1; color:#8b6b52; font-size:13px; line-height:1.8; }
.budget-highlight-card { padding:14px 16px; border-radius:14px; border:1px solid #eadccf; background:#fff; }
.budget-highlight-card.over { border-color:#ffccc7; background:#fff7f7; }
.budget-highlight-card.tip { border-color:#f3dfb3; background:#fffaf0; }
.budget-highlight-card strong { color:#5c3a21; font-size:15px; }
.budget-highlight-card p { margin:6px 0 0; color:#8b6b52; font-size:13px; line-height:1.8; }
.budget-type-grid { display:grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap:12px; }
.budget-type-card { padding:14px; border-radius:14px; border:1px solid #f0dfd1; background:#fff; display:flex; flex-direction:column; gap:8px; }
.budget-type-head, .budget-type-row { display:flex; align-items:center; justify-content:space-between; gap:8px; }
.budget-type-head { color:#8b5a3c; font-weight:600; }
.budget-type-row { color:#8b6b52; font-size:13px; }
.budget-type-row strong { color:#5c3a21; }
.budget-type-progress { display:flex; flex-direction:column; gap:6px; }
.budget-type-progress-bar { height:8px; border-radius:999px; overflow:hidden; background:#f3e7db; }
.budget-type-progress-fill { height:100%; border-radius:999px; background:linear-gradient(90deg,#faad14,#52c41a); transition:width .3s ease; min-width:8px; }
.budget-type-progress-fill.over { background:linear-gradient(90deg,#ff7875,#cf1322); }
.budget-type-progress span { font-size:12px; color:#b08a72; }
.budget-inline-tip { margin:0; color:#b08a72; font-size:12px; }
.prep-panel { display:flex; flex-direction:column; gap:12px; }
.prep-header { display:flex; align-items:flex-start; justify-content:space-between; gap:12px; }
.prep-header h4 { margin:0; font-size:16px; color:#5c3a21; font-family:'STKaiti','楷体','KaiTi',serif; }
.prep-header p { margin:6px 0 0; font-size:13px; color:#b08a72; line-height:1.7; }
.prep-progress-pill { flex-shrink:0; padding:6px 12px; border-radius:999px; background:#f6ffed; color:#389e0d; font-size:12px; font-weight:600; }
.prep-groups { display:flex; flex-direction:column; gap:12px; }
.prep-group-card { padding:14px; border-radius:14px; border:1px solid #f0dfd1; background:linear-gradient(180deg,#fffaf6 0%,#fff 100%); display:flex; flex-direction:column; gap:10px; }
.prep-group-head { display:flex; align-items:flex-start; justify-content:space-between; gap:12px; }
.prep-group-head > div { display:flex; flex-direction:column; gap:4px; }
.prep-group-toggle { border:none; background:transparent; padding:0; text-align:left; cursor:pointer; }
.prep-group-toggle-meta { display:flex; align-items:center; gap:8px; }
.prep-group-arrow { color:#b08a72; font-size:16px; min-width:16px; text-align:center; }
.prep-group-head strong { color:#5c3a21; font-size:15px; }
.prep-group-head span { color:#b08a72; font-size:12px; }
.prep-group-progress { flex-shrink:0; padding:4px 10px; border-radius:999px; background:#f6ffed; color:#389e0d !important; font-size:12px; font-weight:600; }
.prep-list { display:flex; flex-direction:column; gap:8px; }
.prep-item { display:flex; align-items:center; gap:8px; padding:10px 12px; border:1px solid #f0dfd1; border-radius:12px; background:#fff; transition:background .15s; }
.prep-item.done { opacity:.68; }
.prep-item:hover { background:#fffaf6; }
.prep-category-select { width:100px; padding:8px 10px; border:1px solid #e3d3c6; border-radius:10px; background:#fff; color:#8b5a3c; font-size:13px; outline:none; }
.prep-category-select:focus, .prep-name-inp:focus { border-color:#c43b3b; box-shadow:0 0 0 2px rgba(196,59,59,.08); }
.prep-name-inp { flex:1; min-width:0; padding:8px 10px; border:1px solid #e3d3c6; border-radius:10px; background:#fff; color:#5c3a21; font-size:14px; outline:none; }
.prep-name-inp.strike { text-decoration:line-through; color:#b8a088; }
.prep-actions { display:grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap:10px; }
.prep-action-btn { width:100%; }
.detail-notes { background: #fffbe6; border: 1px solid #ffe58f; border-radius: 10px; padding: 14px 18px; margin-bottom: 16px; }
.detail-notes p { margin: 0; font-size: 14px; color: #555; white-space: pre-wrap; }
.detail-images { margin-bottom: 16px; }
.detail-images h4 { font-size: 15px; margin-bottom: 10px; }
.image-grid { display: flex; flex-wrap: wrap; gap: 8px; }
.detail-img { width: 120px; height: 90px; object-fit: cover; border-radius: 8px; cursor: pointer; border: 1px solid #eee; transition: transform 0.15s; }
.detail-img:hover { transform: scale(1.05); }
.detail-day { margin-bottom: 20px; padding: 14px; background: #f9fafb; border-radius: 10px; }
.day-title { margin: 0 0 6px 0; font-size: 16px; }
.day-desc { color: #666; margin: 0 0 8px 0; font-size: 14px; }
.day-section { margin: 6px 0; font-size: 14px; }
.section-label { font-weight: 600; }
.attr-tags { display:flex;flex-wrap:wrap;gap:8px;margin-top:4px }
.attr-link { display:inline-block;padding:6px 14px;background:linear-gradient(135deg,#f0f4ff,#e8f0ff);border:1px solid #b8d0f0;border-radius:16px;font-size:14px;color:#3b6fc4;cursor:pointer;transition:all .15s;font-weight:500 }
.attr-link:hover { background:linear-gradient(135deg,#dce8ff,#d0e0ff);border-color:#80a8e0;transform:translateY(-1px);box-shadow:0 2px 8px rgba(59,111,196,.12) }
.detail-budget { margin-top: 20px; padding: 14px; background: #f0f5ff; border-radius: 10px; }
.detail-budget h4 { margin: 0 0 6px 0; }
.budget-total { margin-top: 6px; font-size: 16px; }
.attr-detail-wrap { display:flex; flex-direction:column; gap:18px; }
.attr-hero-card { display:grid; grid-template-columns: minmax(240px, 320px) 1fr; gap:18px; padding:18px; background:linear-gradient(180deg,#fffaf6 0%,#fff 100%); border:1px solid #eadccf; border-radius:16px; }
.attr-hero-media { min-height:220px; border-radius:14px; overflow:hidden; background:#f6efe7; }
.attr-hero-img { width:100%; height:100%; min-height:220px; object-fit:cover; cursor:pointer; display:block; }
.attr-hero-empty { min-height:220px; display:flex; align-items:center; justify-content:center; text-align:center; padding:20px; border:1px dashed #e2c9b7; border-radius:14px; background:#fcf7f1; color:#b8a088; font-size:14px; }
.attr-hero-main { display:flex; flex-direction:column; gap:16px; }
.attr-hero-head { display:flex; align-items:flex-start; justify-content:space-between; gap:12px; }
.attr-hero-head h3 { margin:0; font-size:24px; color:#5c3a21; font-family:'STKaiti','楷体','KaiTi',serif; }
.attr-hero-head p { margin:6px 0 0; color:#b08a72; font-size:13px; }
.attr-source { flex-shrink:0; padding:5px 10px; border-radius:999px; background:#fdf0e8; color:#c43b3b; font-size:12px; font-weight:600; }
.attr-meta-grid { display:grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap:10px; }
.attr-meta-item { padding:10px 12px; border:1px solid #f2e4d8; border-radius:12px; background:#fffaf6; display:flex; flex-direction:column; gap:4px; }
.attr-meta-label { font-size:12px; color:#b08a72; }
.attr-meta-value { font-size:13px; color:#5c3a21; line-height:1.6; word-break:break-word; }
.attr-map-row { display:flex; }
.attr-map-btn { border:none; border-radius:12px; background:#fdf0e8; color:#c43b3b; padding:10px 14px; font-size:13px; cursor:pointer; transition:all .18s; }
.attr-map-btn:hover { transform:translateY(-1px); box-shadow:0 6px 16px rgba(196,59,59,.1); }
.attr-quick-actions { display:grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap:12px; }
.attr-action-card { display:flex; flex-direction:column; gap:10px; padding:14px; border:1px solid #f0dfd1; border-radius:14px; background:#fff; }
.attr-action-label { font-size:13px; color:#8b5a3c; font-weight:600; }
.attr-action-input, .attr-action-select { width:100%; padding:10px 12px; border:1px solid #e3d3c6; border-radius:10px; background:#fff; color:#5c3a21; font-size:14px; outline:none; }
.attr-action-input:focus, .attr-action-select:focus { border-color:#c43b3b; box-shadow:0 0 0 2px rgba(196,59,59,.08); }
.attr-action-btn { border:none; border-radius:12px; background:#f6efe7; color:#8b5a3c; padding:10px 14px; font-size:14px; cursor:pointer; transition:all .18s; }
.attr-action-btn:hover:not(:disabled) { transform:translateY(-1px); box-shadow:0 6px 16px rgba(139,69,19,.08); }
.attr-action-btn.primary { background:linear-gradient(135deg,#c43b3b,#a0522d); color:#fff; }
.attr-action-btn:disabled { opacity:.55; cursor:not-allowed; box-shadow:none; }
.attr-empty-intro { padding:20px; border-radius:14px; background:#fcf7f1; color:#b8a088; font-size:14px; text-align:center; }
.attr-loading { text-align:center;padding:60px 40px;display:flex;flex-direction:column;align-items:center;gap:20px }
.think-seal { width:56px;height:56px;border-radius:10px;background:#c43b3b;color:#faf0d7;display:flex;align-items:center;justify-content:center;font-size:28px;font-weight:900;font-family:'STKaiti','楷体','KaiTi',serif;animation:pulse 2s infinite ease-in-out }
@keyframes pulse { 0%,100%{transform:scale(1);opacity:1} 50%{transform:scale(1.08);opacity:.7} }
.think-dots { display:flex;gap:6px }
.think-dots span { width:8px;height:8px;border-radius:50%;background:#d4a89a;animation:dotBounce 1.4s infinite ease-in-out both }
.think-dots span:nth-child(2){animation-delay:.16s}.think-dots span:nth-child(3){animation-delay:.32s}
@keyframes dotBounce { 0%,80%,100%{opacity:.3;transform:scale(.8)} 40%{opacity:1;transform:scale(1.2)} }
.think-text { font-size:16px;color:#b8a088;font-family:'STKaiti','楷体','KaiTi',serif;margin:0 }
.attr-intro { font-size: 15px; color: #5c3a21; line-height: 2; }
.attr-intro :deep(h2) { font-size: 22px; font-weight: 700; margin: 20px 0 12px; color: #5c3a21; border-bottom: 2px solid #eadccf; padding-bottom: 8px; }
.attr-intro :deep(h3) { font-size: 18px; font-weight: 700; margin: 16px 0 8px; color: #6b5344; }
.attr-intro :deep(h4) { font-size: 15px; font-weight: 700; margin: 12px 0 6px; }
.attr-intro :deep(strong) { color: #c43b3b; }
.attr-intro :deep(li) { margin: 4px 0; }
.attr-intro :deep(ul) { padding-left: 20px; margin: 8px 0; }
.attr-intro :deep(code) { background: #fdf0e8; padding: 2px 6px; border-radius: 4px; font-size: 13px; }
.memo-modal :deep(.ant-modal-content) { border-radius:16px; overflow:hidden }
.memo-wrap { display:flex;flex-direction:column }
.memo-head { display:flex;align-items:center;gap:14px;padding:24px 28px;background:linear-gradient(135deg,#fdf8f2,#fefaf6);border-bottom:1px solid #eadccf }
.memo-head-icon { font-size:32px }
.memo-head-text h3 { margin:0;font-size:18px;color:#5c3a21;font-family:'STKaiti','楷体','KaiTi',serif }
.memo-head-text span { font-size:12px;color:#b8a088 }
.memo-area { width:100%;min-height:300px;border:none;outline:none;resize:vertical; padding:24px 28px;font-size:16px;line-height:2;color:#5c3a21; background:#fefcf8; background-image:repeating-linear-gradient(#fefcf8 0,#fefcf8 31px,#e8e0d5 31px,#e8e0d5 32px); font-family:'STKaiti','楷体','KaiTi','Georgia',serif }
.memo-area::placeholder { color:#c4b5a5;font-style:italic }
.memo-foot { display:flex;align-items:center;justify-content:space-between;padding:16px 28px;background:#faf7f2;border-top:1px solid #eadccf }
.memo-hint { font-size:13px;color:#b8a088;font-family:'STKaiti','楷体','KaiTi',serif }
.memo-save { padding:8px 22px;border:none;border-radius:18px;background:linear-gradient(135deg,#c43b3b,#a0522d);color:#fff;font-size:14px;cursor:pointer;font-family:'STKaiti','楷体','KaiTi',serif;transition:all .2s }
.memo-save:hover:not(:disabled) { transform:translateY(-1px);box-shadow:0 3px 12px rgba(196,59,59,.3) }
.memo-save:disabled { opacity:.5;cursor:not-allowed }
.memo-attach { padding:0 28px 16px;background:#fefcf8 }
.attach-label { font-size:13px;color:#b8a088;display:block;margin-bottom:8px }
.attach-list { display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px }
.attach-item { display:flex;align-items:center;gap:6px;padding:4px 10px;background:#faf7f2;border:1px solid #eadccf;border-radius:8px;font-size:12px }
.attach-type { font-size:14px }
.attach-name { color:#5c3a21;max-width:120px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis }
.attach-size { color:#b8a088 }
.attach-del { cursor:pointer;color:#ccc;font-size:14px }
.attach-del:hover { color:#c43b3b }
.attach-btns { display:flex;gap:8px }
.attach-btn { padding:6px 14px;border:1px dashed #d4a89a;border-radius:14px;background:transparent;color:#b8a088;font-size:13px;cursor:pointer;transition:all .2s }
.attach-btn:hover { border-color:#c43b3b;color:#c43b3b;background:#fdf8f3 }
.attach-btn.recording { border-color:#ff4d4f;color:#ff4d4f;background:#fff0f0;animation:pulse 1s infinite }
.detail-ai { position:absolute;bottom:20px;right:20px;display:flex;flex-direction:column;align-items:flex-end;gap:8px;z-index:10 }
.detail-ai-bubble { background:#fff;border-radius:12px;padding:10px 16px;max-width:200px;box-shadow:0 4px 16px rgba(139,69,19,.1);font-size:13px;color:#6b5344;line-height:1.5;cursor:pointer;animation:floatIn .4s ease-out;border:1px solid #eadccf }
@keyframes floatIn { from{opacity:0;transform:translateY(8px) scale(.95)} to{opacity:1;transform:translateY(0) scale(1)} }
.detail-ai-btn { width:42px;height:42px;border-radius:50%;background:linear-gradient(135deg,#c43b3b,#a0522d);display:flex;align-items:center;justify-content:center;font-size:20px;cursor:pointer;box-shadow:0 3px 12px rgba(196,59,59,.3);transition:all .2s }
.detail-ai-btn:hover { transform:scale(1.1) }
.empty-seal { width:64px;height:64px;border-radius:12px;background:#c43b3b;color:#faf0d7;display:flex;align-items:center;justify-content:center;font-size:32px;font-weight:900;font-family:'STKaiti','楷体','KaiTi',serif;margin:0 auto 16px }
.empty-title { font-size:20px;font-weight:700;color:#5c3a21;margin:0 0 4px;font-family:'STKaiti','楷体','KaiTi',serif }
.empty-desc { font-size:14px;color:#b8a088;margin:0 0 24px }
.empty-btn { padding:10px 28px;border:1px solid #c43b3b;border-radius:20px;background:#fdf5ee;color:#c43b3b;font-size:15px;cursor:pointer;font-family:'STKaiti','楷体','KaiTi',serif;transition:all .2s }
.empty-btn:hover { background:#c43b3b;color:#fff }
.detail-trip-ops { display:flex; align-items:center; justify-content:space-between; gap:16px; margin:0 0 16px; padding:16px 18px; border:1px solid #eadccf; border-radius:18px; background:linear-gradient(135deg,#fffaf6 0%,#fff 60%,#fdf4ee 100%); box-shadow:0 10px 24px rgba(139,69,19,.05); }
.detail-trip-ops-main { display:flex; flex-direction:column; gap:6px; min-width:0; }
.detail-trip-ops-kicker { font-size:12px; color:#b08a72; letter-spacing:.08em; }
.detail-trip-ops-main strong { font-size:18px; color:#5c3a21; }
.detail-trip-ops-main p { margin:0; color:#8b6b52; font-size:13px; line-height:1.8; }
.detail-trip-ops-actions { display:flex; flex-wrap:wrap; justify-content:flex-end; gap:10px; }
.detail-trip-ops-btn { border:none; border-radius:12px; background:#f6efe7; color:#8b5a3c; padding:10px 14px; font-size:13px; cursor:pointer; transition:all .18s; }
.detail-trip-ops-btn:hover { transform:translateY(-1px); box-shadow:0 6px 16px rgba(139,69,19,.08); }
.detail-trip-ops-btn.primary { background:linear-gradient(135deg,#c43b3b,#a0522d); color:#fff; }
.today-panel { display:flex; flex-direction:column; gap:16px; }
.today-panel-head { display:flex; align-items:flex-start; justify-content:space-between; gap:16px; padding:18px; border-radius:18px; border:1px solid #eadccf; background:linear-gradient(135deg,#fffaf6 0%,#fff 60%,#fdf4ee 100%); }
.today-panel-head h4 { margin:0; font-size:18px; color:#5c3a21; font-family:'STKaiti','楷体','KaiTi',serif; }
.today-panel-head p { margin:8px 0 0; color:#8b6b52; font-size:13px; line-height:1.8; }
.today-day-switcher { display:flex; align-items:center; gap:10px; flex-wrap:wrap; justify-content:flex-end; }
.today-day-btn { border:1px solid #eadccf; border-radius:12px; background:#fff; color:#8b5a3c; padding:9px 12px; font-size:13px; cursor:pointer; transition:all .18s; }
.today-day-btn:hover:not(:disabled) { transform:translateY(-1px); box-shadow:0 6px 16px rgba(139,69,19,.08); }
.today-day-btn:disabled { opacity:.45; cursor:not-allowed; }
.today-day-label { padding:8px 12px; border-radius:999px; background:#fdf0e8; color:#c43b3b; font-size:12px; font-weight:600; }
.today-top-grid { display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:12px; }
.today-card { padding:16px; border-radius:16px; border:1px solid #f0dfd1; background:#fff; display:flex; flex-direction:column; gap:8px; box-shadow:0 8px 20px rgba(139,69,19,.04); }
.today-card.primary { background:linear-gradient(180deg,#fffaf6 0%,#fff 100%); }
.today-card.status { background:linear-gradient(180deg,#f7fff8 0%,#fff 100%); }
.today-card.budget { background:linear-gradient(180deg,#fff7f7 0%,#fff 100%); }
.today-card-kicker { font-size:12px; color:#b08a72; }
.today-card strong { font-size:20px; color:#5c3a21; line-height:1.5; }
.today-card p { margin:0; font-size:13px; color:#8b6b52; line-height:1.8; }
.today-actions-grid { display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); gap:10px; }
.today-action-btn { border:none; border-radius:14px; background:#fff; border:1px solid #f0dfd1; color:#8b5a3c; padding:12px 14px; font-size:13px; cursor:pointer; transition:all .18s; box-shadow:0 6px 16px rgba(139,69,19,.04); }
.today-action-btn:hover { transform:translateY(-1px); box-shadow:0 10px 20px rgba(139,69,19,.08); }
.today-action-btn.accent { background:linear-gradient(135deg,#c43b3b,#a0522d); color:#fff; border-color:transparent; }
.today-task-list { display:flex; flex-direction:column; gap:12px; }
.today-task-card { display:flex; align-items:center; justify-content:space-between; gap:14px; padding:16px; border-radius:16px; border:1px solid #f0dfd1; background:#fff; box-shadow:0 8px 18px rgba(139,69,19,.04); }
.today-task-card.done { background:linear-gradient(180deg,#f7fff8 0%,#fff 100%); opacity:.88; }
.today-task-main { display:flex; flex-direction:column; gap:8px; min-width:0; }
.today-task-meta { display:flex; align-items:center; flex-wrap:wrap; gap:8px; }
.today-task-type { font-size:16px; }
.today-task-meta strong { color:#5c3a21; font-size:15px; }
.today-task-day { padding:4px 10px; border-radius:999px; background:#fcf7f1; color:#b08a72; font-size:12px; }
.today-task-main p { margin:0; color:#8b6b52; font-size:13px; line-height:1.8; }
.today-task-costs { display:flex; flex-wrap:wrap; gap:12px; color:#b08a72; font-size:12px; }
.today-task-actions { display:flex; flex-direction:column; gap:8px; flex-shrink:0; }
.today-mini-btn { border:none; border-radius:12px; background:#f6efe7; color:#8b5a3c; padding:9px 12px; font-size:12px; cursor:pointer; transition:all .18s; }
.today-mini-btn:hover { transform:translateY(-1px); box-shadow:0 6px 14px rgba(139,69,19,.08); }
.today-mini-btn.primary { background:linear-gradient(135deg,#c43b3b,#a0522d); color:#fff; }
.today-attraction-strip { display:flex; flex-direction:column; gap:8px; padding:14px 16px; border-radius:14px; border:1px solid #eadccf; background:#fffaf6; }
.today-attraction-label { font-size:13px; color:#8b5a3c; font-weight:600; }
.trip-info-panel { display:flex; flex-direction:column; gap:14px; margin-bottom:18px; padding:18px; border-radius:18px; border:1px solid #eadccf; background:linear-gradient(135deg,#fffaf6 0%,#fff 60%,#fdf4ee 100%); }
.trip-info-head { display:flex; align-items:flex-start; justify-content:space-between; gap:12px; }
.trip-info-head h4 { margin:0; font-size:18px; color:#5c3a21; font-family:'STKaiti','楷体','KaiTi',serif; }
.trip-info-head p { margin:8px 0 0; font-size:13px; color:#8b6b52; line-height:1.8; }
.trip-info-grid { display:grid; grid-template-columns:repeat(2, minmax(0,1fr)); gap:12px; }
.trip-info-field { display:flex; flex-direction:column; gap:8px; }
.trip-info-field.full { grid-column:1 / -1; }
.trip-info-field span { font-size:13px; color:#8b5a3c; font-weight:600; }
.trip-info-input, .trip-info-textarea { width:100%; border:1px solid #e3d3c6; border-radius:12px; background:#fff; color:#5c3a21; padding:11px 12px; font-size:14px; outline:none; transition:all .18s; }
.trip-info-input:focus, .trip-info-textarea:focus { border-color:#c43b3b; box-shadow:0 0 0 2px rgba(196,59,59,.08); }
.trip-info-textarea { min-height:96px; resize:vertical; line-height:1.7; }
@media (max-width: 1023px) {
  .detail-summary-grid, .detail-overview-strip { grid-template-columns: repeat(2, minmax(0,1fr)); }
  .hero-topbar { flex-wrap: wrap; }
  .detail-hero-aside { width: 100%; min-width: 0; }
  .detail-focus-panel { grid-template-columns: 1fr; }
  .detail-focus-shortcuts { grid-template-columns: repeat(2, minmax(0,1fr)); }
  .today-top-grid { grid-template-columns: 1fr; }
  .today-actions-grid { grid-template-columns: repeat(2, minmax(0,1fr)); }
}
@media (max-width: 767px) {
  .history-detail-shell { padding: 16px; }
  .detail-hero-panel { padding: 16px; border-radius: 20px; }
  .detail-page-topbar, .hero-topbar { flex-direction: column; }
  .detail-page-heading h1 { font-size: 24px; }
  .detail-summary-grid, .detail-overview-strip, .budget-overview, .budget-type-grid, .prep-actions, .attr-quick-actions, .detail-focus-shortcuts { grid-template-columns: 1fr; }
  .detail-heading-badges { gap: 6px; }
  .heading-badge { width: fit-content; }
  .attr-hero-card { grid-template-columns: 1fr; }
  .detail-trip-ops, .today-panel-head, .trip-info-head, .today-task-card { flex-direction:column; align-items:stretch; }
  .detail-trip-ops-actions, .today-day-switcher { justify-content:stretch; }
  .detail-trip-ops-btn, .today-day-btn, .today-mini-btn { width:100%; }
  .today-actions-grid, .trip-info-grid { grid-template-columns:1fr; }
  .today-task-actions { width:100%; }
  .attr-meta-grid { grid-template-columns: 1fr; }
  .task-cost-head { display:none; }
  .task-item { flex-wrap:wrap; align-items:flex-start; }
  .task-day-inp { width:56px; }
  .task-name-inp { min-width: calc(100% - 140px); }
  .task-cost-wrap { margin-left: 28px; }
  .prep-header, .notes-panel-head { flex-direction:column; align-items:stretch; }
  .prep-item { flex-wrap:wrap; }
  .prep-category-select, .prep-name-inp { width:100%; }
  .trip-action-feedback { flex-direction:column; align-items:stretch; }
}
</style>
