import {Divider, theme} from 'antd'
import {typography} from '../utils/typography'

interface DetailSectionDividerProps {
  title: string
}

export default function DetailSectionDivider({ title }: DetailSectionDividerProps) {
  const { token } = theme.useToken()

  return (
    <Divider
      titlePlacement="start"
      styles={{ content: { margin: 0 } }}
      style={{ borderColor: token.colorBorderSecondary }}
    >
      <span style={{ ...typography.sectionHeading, color: token.colorPrimary }}>{title}</span>
    </Divider>
  )
}
