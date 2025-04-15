@echo off
title Bulk image resizer (mirbyte)

set /p confirm="Resize all JPG, JPEG, PNG images in this folder? (y/n): "


if /i "%confirm%"=="Y" (
    echo Starting...
    PowerShell.exe -NoExit -Command "Add-Type -AssemblyName System.Drawing; $formats = @('*.jpg','*.jpeg','*.png'); $count = 0; foreach ($format in $formats) { $files = Get-ChildItem -Path . -Filter $format -File; if ($files) { $files | ForEach-Object { try { $img = [System.Drawing.Image]::FromFile($_.FullName); $newWidth = [int]($img.Width * 0.5); $newHeight = [int]($img.Height * 0.5); $resized = New-Object System.Drawing.Bitmap($newWidth, $newHeight); $graphics = [System.Drawing.Graphics]::FromImage($resized); $graphics.DrawImage($img, 0, 0, $newWidth, $newHeight); $newName = ($_.DirectoryName + '\' + $_.BaseName + '_resized' + $_.Extension); if ($_.Extension -eq '.png') { $resized.Save($newName, [System.Drawing.Imaging.ImageFormat]::Png) } else { $resized.Save($newName, [System.Drawing.Imaging.ImageFormat]::Jpeg) }; $img.Dispose(); $resized.Dispose(); $graphics.Dispose(); $count++; Write-Output ('Processed: ' + $_.Name); } catch { Write-Output ('Error processing: ' + $_.Name); } } } }; if ($count -eq 0) { Write-Output 'No JPG, JPEG or PNG files found!' } else { Write-Output (\"Success! Resized $count image files.\") }"
) else (
    echo Operation cancelled. No images were resized.
)


pause
