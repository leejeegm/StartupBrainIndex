<?php
header('Content-Type: application/json');

$input = json_decode(file_get_contents('php://input'), true);
$imageId = $input['imageId'] ?? '';
$title = $input['title'] ?? '';
$tags = $input['tags'] ?? [];
$description = $input['description'] ?? '';

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

// 메타데이터 업데이트
if (!empty($title)) {
    $metadata['title'] = $title;
}
if (!empty($tags) && is_array($tags)) {
    $metadata['tags'] = $tags;
}
if (!empty($description)) {
    $metadata['description'] = $description;
}
$metadata['updated_at'] = date('Y-m-d H:i:s');

// 메타데이터 파일 저장
$jsonData = json_encode($metadata, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
if ($jsonData === false) {
    echo json_encode(['success' => false, 'message' => '메타데이터 JSON 인코딩 실패.']);
    exit;
}

if (!file_put_contents($metadataFile, $jsonData)) {
    echo json_encode(['success' => false, 'message' => '메타데이터 파일 저장에 실패했습니다.']);
    exit;
}

// 설명 파일도 업데이트
if (!empty($description)) {
    $descriptionFile = 'uploads/' . $imageId . '_description.txt';
    file_put_contents($descriptionFile, $description);
}

echo json_encode([
    'success' => true,
    'message' => '이미지 정보가 수정되었습니다.',
    'metadata' => $metadata
]);
?>
