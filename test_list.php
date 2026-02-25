<?php
// 간단한 테스트 파일 - list_images.php가 작동하는지 확인
header('Content-Type: text/plain; charset=utf-8');

echo "list_images.php 테스트\n";
echo "현재 디렉토리: " . __DIR__ . "\n";
echo "list_images.php 존재 여부: " . (file_exists(__DIR__ . '/list_images.php') ? '예' : '아니오') . "\n";
echo "uploads 디렉토리 존재 여부: " . (file_exists(__DIR__ . '/uploads') ? '예' : '아니오') . "\n";

$pattern = __DIR__ . '/uploads/*_metadata.json';
$files = glob($pattern);
echo "메타데이터 파일 개수: " . count($files) . "\n";

if (count($files) > 0) {
    echo "\n첫 번째 파일: " . $files[0] . "\n";
}
?>
