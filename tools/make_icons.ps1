# 生成 Chrome 插件图标 (16/48/128 PNG)
# 用法: pwsh -File tools/make_icons.ps1
Add-Type -AssemblyName System.Drawing

$outDir = Join-Path $PSScriptRoot "..\extension\icons"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

function New-RoundedRectPath {
  param([float]$x, [float]$y, [float]$w, [float]$h, [float]$r)
  $p = New-Object System.Drawing.Drawing2D.GraphicsPath
  $d = [float]($r * 2)
  $p.AddArc([float]$x, [float]$y, $d, $d, 180, 90)
  $p.AddArc([float]($x + $w - $d), [float]$y, $d, $d, 270, 90)
  $p.AddArc([float]($x + $w - $d), [float]($y + $h - $d), $d, $d, 0, 90)
  $p.AddArc([float]$x, [float]($y + $h - $d), $d, $d, 90, 90)
  $p.CloseFigure()
  return $p
}

function New-Icon([int]$size, [string]$path) {
  $bmp = New-Object System.Drawing.Bitmap $size, $size
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
  $g.Clear([System.Drawing.Color]::Transparent)

  # 背景：蓝色渐变圆角矩形
  $bg = New-RoundedRectPath 0 0 $size $size ($size * 0.22)
  $c1 = [System.Drawing.Color]::FromArgb(255, 30, 144, 255)
  $c2 = [System.Drawing.Color]::FromArgb(255, 0, 60, 180)
  $pt1 = New-Object System.Drawing.Point 0, 0
  $pt2 = New-Object System.Drawing.Point $size, $size
  $brush = New-Object System.Drawing.Drawing2D.LinearGradientBrush -ArgumentList $pt1, $pt2, $c1, $c2
  $g.FillPath($brush, $bg)

  # 白色圆脸
  $fw = $size * 0.62
  $fh = $size * 0.56
  $fx = ($size - $fw) / 2
  $fy = $size * 0.18
  $g.FillEllipse([System.Drawing.Brushes]::White, $fx, $fy, $fw, $fh)

  # 眼睛（深蓝）
  $eyeColor = [System.Drawing.Color]::FromArgb(255, 20, 50, 120)
  $eyeBrush = New-Object System.Drawing.SolidBrush -ArgumentList $eyeColor
  $ew = $size * 0.10
  $eh = $size * 0.16
  $ey = $fy + $fh * 0.32
  $g.FillEllipse($eyeBrush, $fx + $fw * 0.24, $ey, $ew, $eh)
  $g.FillEllipse($eyeBrush, $fx + $fw * 0.66, $ey, $ew, $eh)

  # 微笑
  $pen = New-Object System.Drawing.Pen -ArgumentList $eyeColor, ($size * 0.05)
  $pen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
  $pen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
  $smileW = $size * 0.30
  $smileH = $size * 0.16
  $sx = ($size - $smileW) / 2
  $sy = $fy + $fh * 0.46
  $g.DrawArc($pen, $sx, $sy, $smileW, $smileH, 20, 140)

  $g.Dispose()
  $bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
  $bmp.Dispose()
}

foreach ($s in 16, 48, 128) {
  $p = Join-Path $outDir "icon$s.png"
  New-Icon $s $p
  Write-Host "生成: $p"
}
