$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$assetsDirectory = Join-Path $projectRoot 'assets'
New-Item -ItemType Directory -Force -Path $assetsDirectory | Out-Null

Add-Type -AssemblyName System.Drawing
$size = 256
$bitmap = New-Object System.Drawing.Bitmap($size, $size)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$graphics.Clear([System.Drawing.Color]::FromArgb(35, 40, 61))
$teal = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(137, 190, 200))
$white = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::White)
$soft = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(190, 180, 214))
$pen = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(137, 190, 200), 11)
$pen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
$pen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
$graphics.DrawArc($pen, 39, 33, 178, 178, 190, 160)
$graphics.FillRectangle($teal, 35, 112, 22, 61)
$graphics.FillRectangle($teal, 199, 112, 22, 61)
$cardPen = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(190, 180, 214), 4)
$graphics.DrawRectangle($cardPen, 62, 75, 65, 75)
$graphics.DrawRectangle($cardPen, 129, 107, 65, 75)
$zhFont = New-Object System.Drawing.Font('Microsoft YaHei UI', 31, [System.Drawing.FontStyle]::Bold)
$enFont = New-Object System.Drawing.Font('Segoe UI', 25, [System.Drawing.FontStyle]::Bold)
$format = New-Object System.Drawing.StringFormat
$format.Alignment = [System.Drawing.StringAlignment]::Center
$format.LineAlignment = [System.Drawing.StringAlignment]::Center
$graphics.DrawString('中', $zhFont, $white, (New-Object System.Drawing.RectangleF(62, 75, 65, 75)), $format)
$graphics.DrawString('EN', $enFont, $soft, (New-Object System.Drawing.RectangleF(129, 107, 65, 75)), $format)
$arrowPen = New-Object System.Drawing.Pen([System.Drawing.Color]::White, 7)
$arrowPen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
$graphics.DrawLine($arrowPen, 109, 72, 177, 72)
$graphics.DrawLine($arrowPen, 165, 60, 177, 72)
$graphics.DrawLine($arrowPen, 165, 84, 177, 72)
$graphics.DrawLine($arrowPen, 79, 194, 147, 194)
$graphics.DrawLine($arrowPen, 91, 182, 79, 194)
$graphics.DrawLine($arrowPen, 91, 206, 79, 194)
$graphics.Dispose()

$pngPath = Join-Path $assetsDirectory 'interpreter.png'
$bitmap.Save($pngPath, [System.Drawing.Imaging.ImageFormat]::Png)
$bitmap.Dispose()
$pngBytes = [System.IO.File]::ReadAllBytes($pngPath)
$iconPath = Join-Path $assetsDirectory 'interpreter.ico'
$iconStream = [System.IO.File]::Create($iconPath)
$writer = New-Object System.IO.BinaryWriter($iconStream)
$writer.Write([uint16]0)
$writer.Write([uint16]1)
$writer.Write([uint16]1)
$writer.Write([byte]0)
$writer.Write([byte]0)
$writer.Write([byte]0)
$writer.Write([byte]0)
$writer.Write([uint16]1)
$writer.Write([uint16]32)
$writer.Write([uint32]$pngBytes.Length)
$writer.Write([uint32]22)
$writer.Write($pngBytes)
$writer.Dispose()
$iconStream.Dispose()

$compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
if (-not (Test-Path -LiteralPath $compiler)) {
    throw "Windows C# compiler not found: $compiler"
}
$outputPath = Join-Path $projectRoot 'Interpreter.exe'
$sourcePath = Join-Path $PSScriptRoot 'Launcher.cs'
& $compiler /nologo /target:winexe /platform:anycpu /optimize+ `
    /reference:System.dll /reference:System.Drawing.dll /reference:System.Windows.Forms.dll `
    "/win32icon:$iconPath" "/out:$outputPath" "$sourcePath"
if ($LASTEXITCODE -ne 0) {
    throw "Launcher compilation failed with exit code $LASTEXITCODE"
}

$desktop = [Environment]::GetFolderPath('Desktop')
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut((Join-Path $desktop 'Meeting Interpreter.lnk'))
$shortcut.TargetPath = Join-Path $projectRoot 'Interpreter.exe'
$shortcut.WorkingDirectory = $projectRoot
$shortcut.IconLocation = "$iconPath,0"
$shortcut.Description = 'Private on-device Chinese-English meeting interpreter'
$shortcut.Save()
Write-Output "Launcher: $(Join-Path $projectRoot 'Interpreter.exe')"
Write-Output "Desktop shortcut: $(Join-Path $desktop 'Meeting Interpreter.lnk')"

