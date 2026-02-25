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
        $metadata = @json_decode(file_get_contents($file), true);
        if ($metadata && isset($metadata['image_id']) && $metadata['image_id'] === $imageId) {
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
$imageId = $metadata['image_id'] ?? $imageId;

// 관련 파일들 삭제
$deletedFiles = [];
$filesToDelete = [
    $metadataFile,
    'uploads/' . $imageId . '_text.txt',
    'uploads/' . $imageId . '_description.txt',
    'uploads/' . ($metadata['filename'] ?? $imageId . '.png')
];

foreach ($filesToDelete as $file) {
    if (file_exists($file)) {
        if (@unlink($file)) {
            $deletedFiles[] = $file;
        }
    }
}

echo json_encode([
    'success' => true,
    'message' => '이미지가 삭제되었습니다.',
    'deleted_files' => $deletedFiles
]);
?>
