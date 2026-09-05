import {useCallback, useEffect, useState} from 'react'
import {Outlet, useLocation, useNavigate} from 'react-router-dom'
import {Breadcrumb, Button, Dropdown, Layout, Menu} from 'antd'
import {
    LogoutOutlined,
    MenuFoldOutlined,
    MenuUnfoldOutlined,
    UserOutlined,
} from '@ant-design/icons'
import {BookOpenText, BrainCircuit, BriefcaseBusiness, Fingerprint, LayoutDashboard, Puzzle, Settings, Siren, WandSparkles} from 'lucide-react'
import {useAuthStore} from '../stores/auth'
import {getResourceConfig} from '../config/resources'
import type {ResourceConfig} from '../types/records'
import InboxDrawer from './InboxDrawer'
import RecordDetailModal from './RecordDetailModal'
import {hasPermission} from '../utils/permissions'
import PersonalCenterModal from './PersonalCenterModal'
import UserAvatar from './UserAvatar'
import {palette} from '../palette'
import {wordmarkStyle} from '../utils/typography'

const { Header, Sider, Content } = Layout
const lucideIconProps = {size: '1.2em', strokeWidth: 2}

const breadcrumbMap: Record<string, string> = {
  cases: 'Cases',
  alerts: 'Alerts',
  artifacts: 'Artifacts',
  enrichments: 'Enrichments',
  playbooks: 'Playbooks',
  knowledge: 'Knowledge',
  custom: 'Custom',
  dashboard: 'Dashboard',
  system: 'Setting',
}

export default function MainLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const logout = useAuthStore((s) => s.logout)
  const user = useAuthStore((s) => s.user)
  const [relatedDetail, setRelatedDetail] = useState<{
    config: ResourceConfig
    rowId: string | number
  } | null>(null)
  const [personalCenterOpen, setPersonalCenterOpen] = useState(false)
  const openRelatedDetail = useCallback((resourceKey: string, rowId: string | number) => {
    setRelatedDetail({
      config: getResourceConfig(resourceKey),
      rowId,
    })
  }, [])

  const [collapsed, setCollapsed] = useState(() => {
    return localStorage.getItem('sider-collapsed') === 'true'
  })

  useEffect(() => {
    localStorage.setItem('sider-collapsed', String(collapsed))
  }, [collapsed])

  useEffect(() => {
    const pageKey = location.pathname.split('/').filter(Boolean)[0] || 'cases'
    document.title = `AGUSTA · ${breadcrumbMap[pageKey] || pageKey}`
  }, [location.pathname])

  const selectedKey = (() => {
    const allKeys = ['/dashboard', '/cases', '/alerts', '/artifacts', '/enrichments', '/playbooks', '/knowledge', '/custom', '/system']
    if (allKeys.includes(location.pathname)) return location.pathname
    return '/' + (location.pathname.split('/').filter(Boolean)[0] || 'cases')
  })()
  const isDashboardPage = selectedKey === '/dashboard'

  const menuItems = [
    { key: '/dashboard', icon: <LayoutDashboard {...lucideIconProps} />, label: 'Dashboard' },
    { key: '/cases', icon: <BriefcaseBusiness {...lucideIconProps} />, label: 'Cases' },
    { key: '/alerts', icon: <Siren {...lucideIconProps} />, label: 'Alerts' },
    { key: '/artifacts', icon: <Fingerprint {...lucideIconProps} />, label: 'Artifacts' },
    { key: '/enrichments', icon: <WandSparkles {...lucideIconProps} />, label: 'Enrichments' },
    { key: '/playbooks', icon: <BrainCircuit {...lucideIconProps} />, label: 'Playbooks' },
    { key: '/knowledge', icon: <BookOpenText {...lucideIconProps} />, label: 'Knowledge' },
    hasPermission(user, 'admin') ? { key: '/custom', icon: <Puzzle {...lucideIconProps} />, label: 'Custom' } : null,
    hasPermission(user, 'admin') ? { key: '/system', icon: <Settings {...lucideIconProps} />, label: 'Setting' } : null,
  ].filter((item): item is NonNullable<typeof item> => Boolean(item))

  const pathParts = location.pathname.split('/').filter(Boolean)
  const breadcrumbItems = [
    { title: 'AGUSTA', onClick: () => navigate('/') },
    ...pathParts.map((part, i) => ({
      title: breadcrumbMap[part] || part,
      onClick: i < pathParts.length - 1 ? () => navigate('/' + pathParts.slice(0, i + 1).join('/')) : undefined,
    })),
  ]

  const userMenuItems = [
    { key: 'profile', label: 'Personal', icon: <UserOutlined />, onClick: () => setPersonalCenterOpen(true) },
    { key: 'logout', label: 'Logout', icon: <LogoutOutlined />, onClick: () => { logout(); navigate('/login') } },
  ]

  return (
    <Layout style={{ height: '100vh', minHeight: 0, overflow: 'hidden' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        width={240}
        collapsedWidth={64}
        trigger={null}
        style={{ background: palette.bgLayout, borderRight: `1px solid ${palette.borderSoft}` }}
      >
        <div style={{ height: 48, display: 'flex', alignItems: 'center', justifyContent: 'center', borderBottom: `1px solid ${palette.borderSoft}` }}>
          {collapsed ? (
            <img src="/favicon.svg" alt="logo" style={{ width: 22, height: 22 }} />
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <img src="/favicon.svg" alt="logo" style={{ width: 22, height: 22 }} />
              <span style={{ ...wordmarkStyle, color: palette.text }}>AGUSTA</span>
            </div>
          )}
        </div>
        {/* No `theme="dark"`: that switches Menu onto its darkItem* tokens and
            would bypass the AGUSTA Menu tokens in src/theme.ts. The global
            darkAlgorithm already supplies the dark surface. */}
        <Menu
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ background: 'transparent', borderRight: 'none' }}
        />
        <div style={{ position: 'absolute', bottom: 48, width: '100%', display: 'flex', justifyContent: 'center' }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{ color: palette.textTertiary }}
          />
        </div>
      </Sider>
      <Layout style={{ minHeight: 0 }}>
        <Header style={{
          background: palette.bgContainer,
          padding: '0 16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          height: 48,
          lineHeight: '48px',
          borderBottom: `1px solid ${palette.borderSoft}`,
        }}>
          <Breadcrumb items={breadcrumbItems} />
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <InboxDrawer
              onOpenResource={openRelatedDetail}
            />
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Button type="text" size="large" icon={<UserAvatar username={user?.username} avatarUrl={user?.avatar_url} size={28} />} style={{ color: palette.textSecondary }}>
                {user?.username || 'User'}
              </Button>
            </Dropdown>
          </div>
        </Header>
        <Content style={{ padding: isDashboardPage ? 0 : 16, background: palette.bgBase, minHeight: 0, overflow: 'hidden' }}>
          <Outlet />
        </Content>
        {relatedDetail && (
          <RecordDetailModal
            config={relatedDetail.config}
            rowId={relatedDetail.rowId}
            open
            onOpenResource={openRelatedDetail}
            onClose={() => setRelatedDetail(null)}
          />
        )}
        <PersonalCenterModal open={personalCenterOpen} onClose={() => setPersonalCenterOpen(false)} />
      </Layout>
    </Layout>
  )
}
