import {useState} from 'react'
import {useNavigate, useSearchParams} from 'react-router-dom'
import {BorderBeam, Button, Card, Form, Input, Segmented} from 'antd'
import {message} from '../utils/appMessage'
import {LockOutlined, UserOutlined} from '@ant-design/icons'
import type {AuthType} from '../api/auth'
import {login} from '../api/auth'
import {useAuthStore} from '../stores/auth'
import {getSafeAuthRedirectPath} from '../utils/authRedirect'
import {palette} from '../palette'
import './Login.css'

export default function Login() {
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const setAuth = useAuthStore((s) => s.setAuth)
  const nextPath = getSafeAuthRedirectPath(searchParams.get('next'))

  const onFinish = async (values: { username: string; password: string; auth_type: AuthType }) => {
    setLoading(true)
    try {
      const { data } = await login(values.username, values.password, values.auth_type)
      setAuth(data.access, data.user)
      navigate(nextPath, { replace: true })
    } catch { message.error('Invalid credentials') }
    finally { setLoading(false) }
  }

  return (
    <div className="login-page">
      <div className="login-grid" />
      <section className="login-brand-panel" aria-label="AGUSTA">
        <div className="login-brand-lockup">
          <span className="login-logo-frame">
            <img src="/favicon.svg" alt="" />
          </span>
          <div>
            <div className="login-kicker">AdaptX</div>
            <h1>AGUSTA</h1>
            <p>Agentic security operations, from alert to decision.</p>
          </div>
        </div>
        <ul className="login-highlights">
          <li>
            <strong>Converge the alert flood</strong>
            <span>SIEM and webhook signals resolve into a short list of actionable cases.</span>
          </li>
          <li>
            <strong>Investigate in seconds</strong>
            <span>Agents produce severity, verdicts and a structured report you can audit.</span>
          </li>
          <li>
            <strong>Keep what you learn</strong>
            <span>Every closed case adds reusable knowledge back to the workspace.</span>
          </li>
        </ul>
      </section>
      <BorderBeam
        color={[
          { color: palette.primary, percent: 0 },
          { color: palette.brass, percent: 55 },
          { color: palette.primaryHover, percent: 100 },
        ]}
        outset={0}
      >
        <Card className="login-card">
          <div className="login-card-header">
            <img src="/favicon.svg" alt="" />
            <div>
              <h2>Sign in</h2>
              <p>Use your AGUSTA or LDAP identity.</p>
            </div>
          </div>
          <Form className="login-form" onFinish={onFinish} size="large" initialValues={{ auth_type: 'local' }}>
            <Form.Item name="auth_type" rules={[{ required: true }]}>
              <Segmented
                className="login-auth-switch"
                options={[
                  { label: 'Platform', value: 'local' },
                  { label: 'LDAP', value: 'ldap' },
                ]}
                block
              />
            </Form.Item>
            <Form.Item name="username" rules={[{ required: true }]}>
              <Input prefix={<UserOutlined />} placeholder="Username" />
            </Form.Item>
            <Form.Item name="password" rules={[{ required: true }]}>
              <Input.Password prefix={<LockOutlined />} placeholder="Password" />
            </Form.Item>
            <Form.Item>
              <Button className="login-submit" type="primary" htmlType="submit" loading={loading} block>Log in</Button>
            </Form.Item>
          </Form>
        </Card>
      </BorderBeam>
    </div>
  )
}
