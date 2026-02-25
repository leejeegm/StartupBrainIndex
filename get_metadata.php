<?php
header('Content-Type: application/json');

$input = json_decode(file_get_contents('php://input'), true);
$imageId = $input['imageId'] ?? '';

if (empty($imageId)) {
    echo json_encode(['success' => false, 'message' => '이미지 ID가 없습니다.']);
    exit;
}

// 메타데이터 파일 찾기
$metadataFile = null;
$files = glob('uploads/' . $imageId . '*_metadata.json');

if (empty($files)) {
    $pattern = 'uploads/*_metadata.json';
    $allFiles = glob($pattern);
    
    foreach ($allFiles as $file) {
        $fileMetadata = @json_decode(file_get_contents($file), true);
        if ($fileMetadata && isset($fileMetadata['image_id']) && $fileMetadata['image_id'] === $imageId) {
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

if (!$metadata) {
    echo json_encode(['success' => false, 'message' => '메타데이터를 읽을 수 없습니다.']);
    exit;
}

echo json_encode([
    'success' => true,
    'metadata' => $metadata
]);
?>
