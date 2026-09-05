/**
 * hermes-usage — token-usage bar docked at the BOTTOM of the Hermes UI.
 *
 * Bottom pane (always visible, like a DeepSeek-Harness bottom bar) showing the
 * FOCUSED session's live usage, streamed via host.state.focusedUsage (no
 * backend needed): input / output / cache-hit% / total / calls / cost.
 * Click the bar to open the full /usage detail page (reads state.db via the
 * sibling plugin_api.py backend for per-model & per-session history).
 *
 * Plain ESM, loaded uncompiled — UI is jsx() calls. Only these imports resolve:
 *   @hermes/plugin-sdk, react, react/jsx-runtime
 */

import { host, useValue, haptic, PANES_AREA, ROUTES_AREA, PALETTE_AREA } from '@hermes/plugin-sdk'
import { jsx, jsxs } from 'react/jsx-runtime'
import { useEffect, useState } from 'react'

const ID = 'hermes-usage'
const REFRESH_MS = 20000

/* ---------- number formatting ---------- */
function fmt(n) {
  if (n === null || n === undefined || Number.isNaN(Number(n))) return '—'
  n = Number(n)
  if (n < 0) return '—'
  if (n >= 1e9) return (n / 1e9).toFixed(2) + 'B'
  if (n >= 1e6) return (n / 1e6).toFixed(2) + 'M'
  if (n >= 1e4) return (n / 1e3).toFixed(1) + 'K'
  return Math.round(n).toLocaleString()
}
function fmtUsd(n) {
  if (n === null || n === undefined || n === 0) return '$0'
  if (n < 0.01) return '$' + n.toFixed(4)
  return '$' + n.toFixed(2)
}
function fmtDate(sec) {
  if (!sec) return '—'
  const d = new Date(sec * 1000)
  const p = x => String(x).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

/* ---------- live bottom bar (the always-visible meter) ---------- */
function MeterChip({ label, value, title, strong }) {
  return jsxs('span', {
    className: 'inline-flex items-baseline gap-1 whitespace-nowrap',
    title: title,
    children: [
      jsx('span', { className: 'text-[0.6875rem] text-(--ui-text-quaternary)', children: label }),
      jsx('span', {
        className: strong
          ? 'text-[0.8125rem] font-semibold tabular-nums text-(--ui-accent)'
          : 'text-[0.6875rem] font-medium tabular-nums text-(--ui-text-secondary)',
        children: value
      })
    ]
  })
}

function modelShort(name) {
  if (!name) return '—'
  const s = String(name)
  const i = s.lastIndexOf('/')
  return i >= 0 ? s.slice(i + 1) : s
}

function BottomBar({ loadModels }) {
  const u = useValue(host.state.focusedUsage)
  const model = useValue(host.state.model)
  const storedId = useValue(host.state.focusedStoredSessionId)
  const [models, setModels] = useState(null)
  const open = () => { haptic('tap'); host.navigate('/usage') }

  useEffect(() => {
    let alive = true
    if (!storedId || !loadModels) { setModels(null); return () => { alive = false } }
    const run = () => {
      loadModels(storedId).then(res => {
        if (!alive) return
        setModels(res && res.ok && Array.isArray(res.models) ? res.models : null)
      }).catch(() => { if (alive) setModels(null) })
    }
    run()
    const id = setInterval(run, REFRESH_MS)
    return () => { alive = false; clearInterval(id) }
  }, [storedId, loadModels])

  const multi = models && models.length > 1

  return jsxs('button', {
    type: 'button',
    onClick: open,
    title: '点击打开 Token 用量详情页',
    className: 'flex h-full w-full flex-col justify-center gap-0.5 overflow-hidden px-2 text-left text-(--ui-text-secondary) hover:text-foreground',
    children: [
      !u && !model
        ? jsx('span', { className: 'text-[0.6875rem] text-(--ui-text-tertiary)', children: 'Token 用量 — 暂无活动会话' })
        : jsxs('div', {
            className: 'flex items-center gap-3 overflow-hidden',
            children: [
              jsx('span', {
                className: 'inline-flex max-w-[210px] items-center gap-1 truncate whitespace-nowrap text-[0.6875rem] font-semibold text-(--ui-accent)',
                title: '当前模型: ' + (model || '—'),
                children: model ? '模型 ' + modelShort(model) : '模型 —'
              }),
              u ? jsx(MeterChip, { label: '输入', value: fmt(u.input), title: '输入 token' }) : null,
              u ? jsx(MeterChip, { label: '输出', value: fmt(u.output), title: '输出 token' }) : null,
              u && u.cache_hit_pct != null
                ? jsx(MeterChip, { label: '缓存命中', value: u.cache_hit_pct + '%', title: '当前会话提示词缓存命中率' })
                : null,
              u ? jsx(MeterChip, { label: '总', value: fmt(u.total), title: '总 token（含缓存）', strong: true }) : null,
              u ? jsx(MeterChip, { label: '调用', value: u.calls ?? 0, title: 'API 调用次数' }) : null,
              u && u.cost_usd != null ? jsx(MeterChip, { label: '费用', value: fmtUsd(u.cost_usd), title: '估算费用 USD' }) : null,
              multi ? jsx('span', { className: 'whitespace-nowrap text-[0.6875rem] text-(--ui-text-tertiary)', children: '· ' + models.length + ' 个模型' }) : null
            ]
          }),
      multi
        ? jsxs('div', {
            className: 'flex items-center gap-2 overflow-hidden',
            children: [
              jsx('span', { className: 'whitespace-nowrap text-[0.6875rem] text-(--ui-text-quaternary)', children: '本会话按模型:' }),
              models.map(mm => jsxs('span', {
                className: 'inline-flex items-center gap-1 whitespace-nowrap rounded bg-(--ui-bg-elevated) px-1.5 py-px text-[0.6875rem]',
                title: (mm.provider ? mm.provider + ' · ' : '') + (mm.model || '') + ' · 总 ' + (mm.total != null ? mm.total.toLocaleString() : '') + ' · ' + (mm.calls || 0) + ' 次调用',
                children: [
                  jsx('span', { className: 'text-(--ui-text-secondary)', children: modelShort(mm.model) }),
                  jsx('span', { className: 'font-medium tabular-nums text-(--ui-text-tertiary)', children: fmt(mm.total) })
                ]
              }, (mm.model || '') + '·' + String(mm.calls)))
            ]
          })
        : null
    ]
  })
}

/* ---------- detail page (/usage) — reads state.db via backend ---------- */
function StatCard({ label, value, sub, accent }) {
  return jsxs('div', {
    className: 'flex flex-col gap-1 rounded-md border border-(--ui-stroke-secondary) bg-(--ui-bg-elevated) p-3',
    children: [
      jsx('div', { className: 'text-[0.6875rem] uppercase tracking-wide text-(--ui-text-tertiary)', children: label }),
      jsx('div', {
        className: accent ? 'text-xl font-semibold text-(--ui-accent)' : 'text-xl font-semibold tabular-nums',
        title: value,
        children: value
      }),
      sub ? jsx('div', { className: 'text-[0.6875rem] text-(--ui-text-tertiary)', children: sub }) : null
    ]
  })
}

function UsagePage({ load }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const [asof, setAsof] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let alive = true
    const run = () => {
      load().then(res => {
        if (!alive) return
        setData(res)
        setError(res && res.ok === false ? (res.error || 'usage backend error') : null)
        setAsof(new Date())
      }).catch(e => {
        if (!alive) return
        setData(null)
        setError((e && e.message) || String(e))
      }).finally(() => { if (alive) setLoading(false) })
    }
    run()
    const id = setInterval(run, REFRESH_MS)
    return () => { alive = false; clearInterval(id) }
  }, [load, reloadKey])

  if (loading && !data && !error) {
    return jsx('div', { className: 'flex h-full items-center justify-center p-8 text-sm text-(--ui-text-tertiary)', children: '加载用量数据…' })
  }
  if (error) {
    return jsxs('div', {
      className: 'flex h-full flex-col items-start justify-center gap-3 p-8',
      children: [
        jsx('div', { className: 'text-sm font-medium', children: '无法读取用量后端' }),
        jsx('pre', { className: 'max-w-full whitespace-pre-wrap rounded-md border border-(--ui-stroke-secondary) bg-(--ui-bg-elevated) p-3 text-xs text-(--ui-text-secondary)', children: error }),
        jsx('div', { className: 'text-xs text-(--ui-text-tertiary)', children: '后端需加入 plugins.enabled 白名单并在 gateway 重启后挂载。底部条(实时)不依赖它，本页(历史)依赖它。' }),
        jsx('button', {
          type: 'button',
          className: 'rounded-md bg-(--ui-accent) px-3 py-1.5 text-sm hover:opacity-90',
          onClick: () => { setReloadKey(k => k + 1); setLoading(true) },
          children: '重试'
        })
      ]
    })
  }

  const t = (data && data.totals) || {}
  const meta = (data && data.meta) || {}
  const perModel = (data && data.per_model) || []
  const perSession = (data && data.per_session) || []
  const daily = ((data && data.daily) || []).filter(d => d.active)
  const cacheRatio = t.cache_share_of_input

  return jsxs('div', {
    className: 'flex h-full flex-col gap-4 overflow-y-auto p-4',
    children: [
      jsxs('div', {
        className: 'flex flex-wrap items-center gap-3',
        children: [
          jsx('div', { className: 'text-base font-semibold', children: 'Token 用量' }),
          jsx('span', { className: 'rounded bg-(--ui-bg-elevated) px-1.5 py-0.5 text-[0.6875rem] text-(--ui-text-secondary)',
            children: `${meta.models || 0} models · ${meta.sessions || 0} sessions · ${meta.api_calls || 0} calls` }),
          jsx('span', { className: 'text-[0.6875rem] text-(--ui-text-tertiary)',
            children: asof ? '更新于 ' + fmtDate(asof.getTime() / 1000) : '' }),
          jsx('button', {
            type: 'button',
            className: 'ml-auto rounded-md border border-(--ui-stroke-secondary) px-2 py-1 text-xs hover:bg-(--chrome-action-hover)',
            onClick: () => { setReloadKey(k => k + 1); setLoading(true) },
            children: '刷新'
          })
        ]
      }),
      jsxs('div', {
        className: 'grid grid-cols-2 gap-2 md:grid-cols-4',
        children: [
          jsx(StatCard, { label: '总 Token', value: fmt(t.total), sub: String(t.total ?? ''), accent: true }),
          jsx(StatCard, { label: '输入', value: fmt(t.input), sub: String(t.input ?? '') }),
          jsx(StatCard, { label: '输出', value: fmt(t.output), sub: String(t.output ?? '') }),
          jsx(StatCard, { label: '缓存读取', value: fmt(t.cache_read), sub: String(t.cache_read ?? '') }),
          jsx(StatCard, { label: '推理', value: fmt(t.reasoning), sub: String(t.reasoning ?? '') }),
          jsx(StatCard, { label: '估算费用', value: fmtUsd(t.est_usd), sub: `${meta.est_rows || 0} 路由计入费率`, accent: true }),
          jsx(StatCard, { label: 'API 调用', value: fmt(t.api_calls), sub: '' }),
          jsx(StatCard, { label: '缓存 ÷ 输入', value: cacheRatio == null ? '—' : cacheRatio.toFixed(1) + 'x',
            sub: cacheRatio == null ? '无数据' : '读取放大倍数（非命中率）' })
        ]
      }),
      jsxs('div', {
        className: 'rounded-md border border-(--ui-stroke-secondary) bg-(--ui-bg-elevated) p-3',
        children: [
          jsxs('div', { className: 'mb-2 flex items-baseline gap-2',
            children: [ jsx('div', { className: 'text-sm font-medium', children: '近 30 天趋势' }),
              jsx('span', { className: 'text-[0.6875rem] text-(--ui-text-tertiary)', children: `${daily.length} 个有量日` }) ] }),
          daily.length === 0
            ? jsx('div', { className: 'py-4 text-center text-[0.8125rem] text-(--ui-text-tertiary)', children: '近 30 天没有用量记录' })
            : jsxs('div', {
                className: 'flex flex-col gap-1',
                children: daily.slice(-14).map(d => {
                  const mx = Math.max(...daily.map(x => x.total || 0), 1)
                  return jsxs('div', {
                    className: 'flex items-center gap-2',
                    children: [
                      jsx('span', { className: 'w-16 shrink-0 text-[0.6875rem] tabular-nums text-(--ui-text-tertiary)', children: d.date.slice(5) }),
                      jsx('div', { className: 'flex flex-1 gap-0.5',
                        children: [
                          jsx('div', { className: 'h-2 rounded-sm bg-(--ui-accent) opacity-60', style: { width: Math.max((d.cache_read || 0) / mx, 0.004) * 100 + '%' } }),
                          jsx('div', { className: 'h-2 rounded-sm bg-(--ui-accent)', style: { width: Math.max((d.output || 0) / mx, 0.004) * 100 + '%' } })
                        ] }),
                      jsx('span', { className: 'w-14 shrink-0 text-right text-[0.6875rem] tabular-nums text-(--ui-text-secondary)', title: 'total ' + (d.total ?? 0), children: fmt(d.total) })
                    ]
                  }, d.date)
                })
              })
        ]
      }),
      jsxs('div', {
        className: 'rounded-md border border-(--ui-stroke-secondary) bg-(--ui-bg-elevated) p-3',
        children: [
          jsx('div', { className: 'mb-2 text-sm font-medium', children: '按模型' }),
          perModel.length === 0
            ? jsx('div', { className: 'py-3 text-center text-[0.8125rem] text-(--ui-text-tertiary)', children: '暂无数据' })
            : jsx('table', {
                className: 'w-full border-collapse text-[0.8125rem]',
                children: jsxs('tbody', {
                  children: perModel.map((m, i) => jsxs('tr', {
                    className: 'border-b border-(--ui-stroke-secondary) last:border-0',
                    children: [
                      jsx('td', { className: 'py-1.5 pr-2', children: jsxs('div', { className: 'flex flex-col',
                        children: [
                          jsx('span', { className: 'font-medium', children: m.model || '—' }),
                          m.provider ? jsx('span', { className: 'text-[0.6875rem] text-(--ui-text-tertiary)', children: m.provider }) : null
                        ] }) }),
                      tc(m.calls, '调用'),
                      tc(m.input, '输入'),
                      tc(m.output, '输出'),
                      tc(m.cache_read, '缓存'),
                      tc(m.reasoning, '推理'),
                      tc(m.est_usd == null ? null : fmtUsd(m.est_usd), '费用')
                    ]
                  }, (m.provider || '') + '·' + (m.model || '') + '·' + i))
                })
              })
        ]
      }),
      jsxs('div', {
        className: 'rounded-md border border-(--ui-stroke-secondary) bg-(--ui-bg-elevated) p-3',
        children: [
          jsx('div', { className: 'mb-2 text-sm font-medium', children: '按会话（Top 30）' }),
          perSession.length === 0
            ? jsx('div', { className: 'py-3 text-center text-[0.8125rem] text-(--ui-text-tertiary)', children: '暂无数据' })
            : jsx('table', {
                className: 'w-full border-collapse text-[0.8125rem]',
                children: jsxs('tbody', {
                  children: perSession.map((s, i) => jsxs('tr', {
                    className: 'border-b border-(--ui-stroke-secondary) last:border-0',
                    children: [
                      jsx('td', { className: 'max-w-[240px] py-1.5 pr-2', children: jsxs('div', { className: 'flex flex-col',
                        children: [
                          jsx('span', { className: 'truncate font-medium', title: s.title || s.session_id, children: s.title || s.session_id }),
                          jsx('span', { className: 'text-[0.6875rem] text-(--ui-text-tertiary)',
                            children: (s.model || '') + (s.provider ? ' · ' + s.provider : '') + ' · ' + fmtDate(s.last_activity_at || s.started_at) })
                        ] }) }),
                      tc(s.calls, '调用'),
                      tc(s.total, '总'),
                      tc(s.input, '输入'),
                      tc(s.output, '输出'),
                      tc(s.cache_read, '缓存'),
                      tc(s.est_usd == null ? null : fmtUsd(s.est_usd), '费用')
                    ]
                  }, (s.session_id || 's') + '·' + i))
                })
              })
        ]
      })
    ]
  })
}

function tc(v, label) {
  return jsx('td', {
    className: 'py-1.5 px-1 text-right tabular-nums text-(--ui-text-secondary)',
    title: label,
    children: v == null ? '—' : v
  })
}

/* ---------- plugin export ---------- */
export default {
  id: ID,
  name: 'Token 用量',
  register(ctx) {
    const load = () => ctx.rest('/overview')
    const loadModels = sid => ctx.rest('/session_models?session_id=' + encodeURIComponent(String(sid || '')))

    // Always-visible bottom meter (auto-docked below the workspace pane).
    ctx.register({
      id: 'pane',
      area: PANES_AREA,
      title: 'Token 用量',
      data: { placement: 'bottom', dock: { pane: 'workspace', pos: 'bottom' }, height: '56px' },
      render: () => jsx(BottomBar, { loadModels })
    })

    // Detail page (clicking the bar opens it).
    ctx.register({
      id: 'page',
      area: ROUTES_AREA,
      data: { path: '/usage' },
      render: () => jsx(UsagePage, { load })
    })

    ctx.register({
      id: 'open',
      area: PALETTE_AREA,
      data: {
        id: 'hermes-usage.open',
        label: '打开 Token 用量',
        keywords: ['usage', 'token', '用量'],
        run: () => { haptic('tap'); host.navigate('/usage') }
      }
    })
  }
}
