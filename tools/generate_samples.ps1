param(
    [string]$OutputDirectory = (Join-Path $PSScriptRoot '..\samples')
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null

$samples = @(
    @{ Name = 'meeting-zh.wav'; Voice = 'Microsoft Huihui Desktop'; Text = '你好，很高兴参加今天的会议。请确认订单中的乘客姓名、航班号和到达时间是否正确。我们明天上午十点讨论下一版本的发布计划。' },
    @{ Name = 'meeting-en.wav'; Voice = 'Microsoft Zira Desktop'; Text = "Hello, it is a pleasure to join today's meeting. Please confirm that the passenger name, flight number, and arrival time are correct. We will discuss the next release plan at ten tomorrow morning." }
)

foreach ($sample in $samples) {
    $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
    try {
        $synth.SelectVoice($sample.Voice)
        $synth.Rate = 0
        $synth.SetOutputToWaveFile((Join-Path $OutputDirectory $sample.Name))
        $synth.Speak($sample.Text)
    }
    finally {
        $synth.Dispose()
    }
}


