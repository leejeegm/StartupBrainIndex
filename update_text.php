<?php
header('Content-Type: application/json');

$input = json_decode(file_get_contents('php://input'), true);
$imageId = $input['imageId'] ?? '';
$text = $input['text'] ?? '';

if (empty($imageId) || empty($text)) {
    echo json_encode(['success' => false, 'message' => '이미지 ID 또는 텍스트가 없습니다.']);
    exit;
}

// 메타데이터 파일 찾기
$metadataFile = null;
$files = glob('uploads/' . $imageId . '*_metadata.json');

if (empty($files)) {
    // 이미지 ID로 직접 찾기
    $pattern = 'uploads/*_metadata.json';
    $allFiles = glob($pattern);
    
    foreach ($allFiles as $file) {
        $metadata = json_decode(file_get_contents($file), true);
        if (isset($metadata['image_id']) && $metadata['image_id'] === $imageId) {
            $metadataFile = $file;
            break;
        }
    }
} else {
    $metadataFile = $files[0];
}

if (!$metadataFile || !file_exists($metadataFile)) {
    echo json_encode(['success' => false, 'message' => '메타데이터 파일을 찾을 수 없습니다.']);
    exit;
}

$metadata = json_decode(file_get_contents($metadataFile), true);

// 텍스트 업데이트
$metadata['text'] = $text;
$metadata['updated_at'] = date('Y-m-d H:i:s');

// 메타데이터 파일 업데이트
if (file_put_contents($metadataFile, json_encode($metadata, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT))) {
    // 텍스트 파일도 업데이트
    $textFile = dirname($metadataFile) . '/' . $metadata['image_id'] . '_text.txt';
    file_put_contents($textFile, $text);
    
    echo json_encode(['success' => true, 'message' => '텍스트가 수정되었습니다.']);
} else {
    echo json_encode(['success' => false, 'message' => '텍스트 수정에 실패했습니다.']);
}
?>
