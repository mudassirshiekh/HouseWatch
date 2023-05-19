// @ts-nocheck
import * as React from 'react'
import { usePollingEffect } from './PageCacheHits'
import { Line } from '@ant-design/plots'
import { highlight, languages } from 'prismjs/components/prism-core'
import 'prismjs/components/prism-sql'
import 'prismjs/components/prism-yaml'
import 'prismjs/themes/prism.css'
import Editor from 'react-simple-code-editor'
import { Tab, Tabs } from '@mui/material'
import { format } from 'sql-formatter-plus'
import { Button, Card, Col, Row, Spin, Table, Tooltip } from 'antd'
import { InfoCircleOutlined } from '@ant-design/icons'
import { useHistory } from 'react-router-dom'

export default function QueryDetail({ match }) {
    const [tab, setTab] = React.useState('query')
    const [queryDetail, setQueryDetail] = React.useState([])
    const [querySQL, setQuerySQL] = React.useState('')
    const [data, setData] = React.useState({})
    const history = useHistory()
    const [showCopiedToClipboardNotice, setShowCopiedToClipboardNotice] = React.useState(false)



    const defaultConfig = {
        data: queryDetail,
        padding: 'auto',
        xField: 'day_start',
        yField: 'total',
    }
    const [config, setConfig] = React.useState(defaultConfig)

    const url = `http://localhost:8000/api/analyze/${match.params.query_hash}/query_detail`

    usePollingEffect(
        async () =>
            setQueryDetail(
                await fetch(url)
                    .then((response) => {
                        return response.json()
                    })
                    .then((data) => {
                        setData(data)
                        const mappedData = data.execution_count
                        setConfig({ ...config, data: mappedData })
                        setQuerySQL(data.query)
                        return mappedData
                    })
                    .catch((err) => {
                        return []
                    })
            ),
        [],
        { interval: 5000 } // optional
    )


    const copyToClipboard = (value) => {
        navigator.clipboard.writeText(value)
        setShowCopiedToClipboardNotice(true)
        setTimeout(() => setShowCopiedToClipboardNotice(false), 1000)
    }

    let index = 0
    return (
        <>
            <a onClick={() => history.push(`/slow_queries/`)}>← Return to queries list</a>
            <h1>Query analyzer</h1>
            <Tabs value={tab} textColor="primary" indicatorColor="primary" onChange={(_, value) => setTab(value)}>
                <Tab value="query" label="Query" />
                <Tab value="metrics" label="Metrics" />
                <Tab value="explain" label="EXPLAIN" />
                <Tab value="examples" label="Example queries" />
            </Tabs>
            <br />
            <div style={{ height: 20, maxHeight: 20 }}>
                {showCopiedToClipboardNotice ? <p style={{ textAlign: 'center', fontSize: 10, color: '#554e4e', lineHeight: 0, margin: 0, padding: 0 }}>Copied to clipboard!</p> : null}
            </div>
            {!data.query ? (
                <div style={{ height: 500 }}>
                    <Spin size='large' style={{ margin: 'auto', display: 'block', marginTop: 50 }} />
                </div>
            ) :
                tab === 'query' ? (
                    <div onClick={() => copyToClipboard(querySQL)}
                    >
                        <Editor
                            value={format(
                                querySQL.replace(/(\?)/g, () => {
                                    index = index + 1
                                    return '$' + index
                                })
                            )}
                            onValueChange={(code) => setSql(format(code))}
                            highlight={(code) => highlight(code, languages.sql)}
                            padding={10}
                            style={{
                                fontFamily: '"Fira code", "Fira Mono", monospace',
                                fontSize: 16,
                                border: '1px solid rgb(216, 216, 216)',
                                borderRadius: 4,
                                boxShadow: '2px 2px 2px 2px rgb(217 208 208 / 20%)',
                                marginBottom: 5,
                            }}
                            multiline
                            disabled
                            className='code-editor'
                        />
                    </div>
                ) : tab === 'metrics' ? (
                    <>
                        <br />
                        <Row gutter={8} style={{ paddingBottom: 8 }}>
                            <Col span={12}>
                                <Card style={{ boxShadow: '2px 2px 2px 2px rgb(217 208 208 / 20%)' }} title="Number of queries">
                                    <Line
                                        data={data.execution_count.map((dataPoint) => ({
                                            ...dataPoint,
                                            day_start: dataPoint.day_start.split('T')[0],
                                        }))}
                                        xField={'day_start'}
                                        yField={'total'}
                                        xAxis={{ tickCount: 5 }}
                                        style={{ padding: 20, height: 300 }}
                                        color="#ffb200"
                                    />
                                </Card>
                            </Col>
                            <Col span={12}>
                                <Card style={{ boxShadow: '2px 2px 2px 2px rgb(217 208 208 / 20%)' }} title="Data read (GB)">
                                    <Line
                                        data={data.read_bytes.map((dataPoint) => ({
                                            day_start: dataPoint.day_start.split('T')[0],
                                            total: dataPoint.total / 1000000000,
                                        }))}
                                        xField={'day_start'}
                                        yField={'total'}
                                        xAxis={{ tickCount: 5 }}
                                        style={{ padding: 20, height: 300 }}
                                        color="#ffb200"
                                    />
                                </Card>
                            </Col>
                        </Row>
                        <Row gutter={8}>
                            <Col span={12}>
                                <Card style={{ boxShadow: '2px 2px 2px 2px rgb(217 208 208 / 20%)' }} title="Memory usage (GB)">
                                    <Line
                                        data={data.memory_usage.map((dataPoint) => ({
                                            day_start: dataPoint.day_start.split('T')[0],
                                            total: dataPoint.total / 1000000000,
                                        }))}
                                        xField={'day_start'}
                                        yField={'total'}
                                        style={{ padding: 20, height: 300 }}
                                        color="#ffb200"
                                    />
                                </Card>
                            </Col>
                            <Col span={12}>
                                <Card
                                    style={{ boxShadow: '2px 2px 2px 2px rgb(217 208 208 / 20%)' }}
                                    title={
                                        <>
                                            CPU usage (seconds){' '}
                                            <Tooltip
                                                title={`Calculated from OSCPUVirtualTimeMicroseconds metric from ClickHouse query log's ProfileEvents.`}
                                            >
                                                <InfoCircleOutlined />
                                            </Tooltip>
                                        </>
                                    }
                                >
                                    <Line
                                        data={data.cpu.map((dataPoint) => ({
                                            day_start: dataPoint.day_start.split('T')[0],
                                            total: dataPoint.total,
                                        }))}
                                        xField={'day_start'}
                                        yField={'total'}
                                        style={{ padding: 20, height: 300 }}
                                        color="#ffb200"
                                    />
                                </Card>
                            </Col>
                        </Row>
                    </>
                ) : tab === 'explain' ? (
                    <div onClick={() => copyToClipboard((data.explain || [{ explain: '' }]).map((row) => row.explain).join('\n'))}>

                        <Editor
                            value={(data.explain || [{ explain: '' }]).map((row) => row.explain).join('\n')}
                            onValueChange={() => { }}
                            highlight={(code) => highlight(code, languages.yaml)}
                            padding={10}
                            style={{
                                fontFamily: '"Fira code", "Fira Mono", monospace',
                                fontSize: 12,
                                border: '1px solid rgb(216, 216, 216)',
                                borderRadius: 4,
                                boxShadow: '2px 2px 2px 2px rgb(217 208 208 / 20%)',
                                marginBottom: 5,
                            }}
                            multiline
                            disabled
                            className='code-editor'
                        />
                    </div>
                ) : tab === 'examples' ? (
                    <Table
                        columns={[
                            {
                                title: 'Query',
                                dataIndex: 'query',
                                render: (_, item) => (
                                    <Editor
                                        value={item.query}
                                        onValueChange={() => { }}
                                        highlight={(code) => highlight(code, languages.sql)}
                                        padding={10}
                                        style={{
                                            fontFamily: '"Fira code", "Fira Mono", monospace',
                                        }}
                                        multiline
                                        disabled
                                    />
                                ),
                            },
                        ]}
                        dataSource={data.example_queries}
                    />
                ) : null}
            <br />
        </>
    )
}
