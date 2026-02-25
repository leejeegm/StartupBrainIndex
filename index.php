<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>텍스트 to 이미지 생성기</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 30px;
        }

        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
            font-size: 2.5em;
        }

        .input-section {
            margin-bottom: 30px;
        }

        .input-group {
            margin-bottom: 20px;
        }

        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 600;
        }

        textarea {
            width: 100%;
            min-height: 120px;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 10px;
            font-size: 16px;
            resize: vertical;
            transition: border-color 0.3s;
        }

        textarea:focus {
            outline: none;
            border-color: #667eea;
        }

        .drop-zone {
            border: 3px dashed #667eea;
            border-radius: 15px;
            padding: 40px;
            text-align: center;
            background: #f8f9ff;
            transition: all 0.3s;
            cursor: pointer;
        }

        .drop-zone:hover {
            background: #f0f2ff;
            border-color: #764ba2;
        }

        .drop-zone.dragover {
            background: #e8ebff;
            border-color: #764ba2;
            transform: scale(1.02);
        }

        .drop-zone p {
            color: #666;
            font-size: 18px;
            margin: 10px 0;
        }

        .btn {
            padding: 12px 30px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            margin: 5px;
        }

        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }

        .btn-secondary {
            background: #6c757d;
            color: white;
        }

        .btn-secondary:hover {
            background: #5a6268;
        }

        .btn-success {
            background: #28a745;
            color: white;
        }

        .btn-success:hover {
            background: #218838;
        }

        .btn-danger {
            background: #dc3545;
            color: white;
        }

        .btn-danger:hover {
            background: #c82333;
        }

        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        .image-section {
            margin-top: 30px;
        }

        .image-container {
            text-align: center;
            margin-bottom: 20px;
        }

        .generated-image {
            max-width: 100%;
            max-height: 600px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin: 20px 0;
        }

        .description-box {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            border-left: 4px solid #667eea;
        }

        .description-box h3 {
            color: #333;
            margin-bottom: 10px;
        }

        .description-box p {
            color: #666;
            line-height: 1.6;
            white-space: pre-wrap;
        }

        .loading {
            text-align: center;
            padding: 40px;
            color: #667eea;
            font-size: 18px;
        }

        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #dc3545;
        }

        .search-section {
            margin-bottom: 20px;
        }

        .search-box {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }

        .search-box input {
            flex: 1;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
        }

        .search-results {
            margin-top: 20px;
        }

        .result-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
            border-left: 4px solid #667eea;
        }

        .result-item h4 {
            color: #333;
            margin-bottom: 5px;
        }

        .result-item p {
            color: #666;
            font-size: 14px;
        }

        .action-buttons {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 20px;
        }

        .edit-text-area {
            display: none;
            margin-top: 10px;
        }

        .edit-text-area.active {
            display: block;
        }

        .title-suggestion-box {
            background: #f0f7ff;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            border-left: 4px solid #667eea;
        }

        .title-suggestion-box h3 {
            color: #333;
            margin-bottom: 10px;
        }

        .title-suggestions {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .title-suggestion-item {
            background: white;
            padding: 15px;
            border-radius: 8px;
            border: 2px solid #ddd;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .title-suggestion-item:hover {
            border-color: #667eea;
            background: #f8f9ff;
            transform: translateX(5px);
        }

        .title-suggestion-item.selected {
            border-color: #667eea;
            background: #e8ebff;
            font-weight: 600;
        }

        .title-suggestion-item .title-text {
            flex: 1;
            color: #333;
            font-size: 16px;
        }

        .title-suggestion-item .check-icon {
            color: #667eea;
            font-size: 20px;
            display: none;
        }

        .title-suggestion-item.selected .check-icon {
            display: block;
        }

        .current-title-box {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            border-left: 4px solid #28a745;
        }

        .current-title-box h3 {
            color: #333;
            margin-bottom: 10px;
        }

        .saved-images-section {
            margin-top: 40px;
            padding-top: 30px;
            border-top: 2px solid #eee;
        }

        .saved-images-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }

        .saved-images-header h2 {
            color: #333;
            margin: 0;
        }

        .images-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }

        .image-card {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 15px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
        }

        .image-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }

        .image-card img {
            width: 100%;
            height: 200px;
            object-fit: cover;
            border-radius: 8px;
            margin-bottom: 10px;
        }

        .image-card-title {
            font-weight: 600;
            color: #333;
            margin-bottom: 5px;
            font-size: 16px;
        }

        .image-card-text {
            color: #666;
            font-size: 14px;
            margin-bottom: 10px;
            overflow: hidden;
            text-overflow: ellipsis;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
        }

        .image-card-date {
            color: #999;
            font-size: 12px;
            margin-bottom: 10px;
        }

        .image-card-actions {
            display: flex;
            gap: 5px;
            flex-wrap: wrap;
        }

        .image-card-actions .btn {
            padding: 6px 12px;
            font-size: 14px;
        }

        .edit-metadata-form {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-top: 15px;
            display: none;
        }

        .edit-metadata-form.active {
            display: block;
        }

        .edit-metadata-form input,
        .edit-metadata-form textarea {
            width: 100%;
            padding: 10px;
            margin-bottom: 10px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
        }

        .edit-metadata-form label {
            display: block;
            margin-bottom: 5px;
            color: #555;
            font-weight: 600;
        }

        .tags-input {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            margin-bottom: 10px;
        }

        .tag {
            background: #667eea;
            color: white;
            padding: 4px 10px;
            border-radius: 15px;
            font-size: 12px;
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .tag-remove {
            cursor: pointer;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎨 텍스트 to 이미지 생성기</h1>

        <div class="input-section">
            <div class="input-group">
                <label for="textInput">텍스트 입력:</label>
                <textarea id="textInput" placeholder="이미지를 생성할 텍스트를 입력하세요..."></textarea>
            </div>

            <div class="input-group">
                <label>또는 파일 드래그 앤 드롭:</label>
                <div class="drop-zone" id="dropZone">
                    <p>📁 파일을 여기에 드래그 앤 드롭하세요</p>
                    <p style="font-size: 14px; color: #999;">또는 클릭하여 파일 선택</p>
                    <input type="file" id="fileInput" style="display: none;" accept=".txt,.md,.doc,.docx">
                </div>
            </div>

            <div class="search-section">
                <div class="search-box">
                    <input type="text" id="searchInput" placeholder="키워드로 검색...">
                    <button class="btn btn-secondary" onclick="searchImages()">검색</button>
                </div>
                <div id="searchResults" class="search-results"></div>
            </div>

            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                <button class="btn btn-primary" onclick="generateImage()">이미지 생성</button>
                <button class="btn btn-secondary" onclick="loadSavedImages()">📚 저장된 이미지 보기</button>
            </div>
        </div>

        <div id="loading" class="loading" style="display: none;">
            <div class="spinner"></div>
            <p>이미지를 생성하는 중...</p>
        </div>

        <div id="error" class="error" style="display: none;"></div>

        <div class="saved-images-section" id="savedImagesSection" style="display: none;">
            <div class="saved-images-header">
                <h2>📚 저장된 이미지</h2>
                <button class="btn btn-secondary" onclick="closeSavedImages()">닫기</button>
            </div>
            <div id="imagesGrid" class="images-grid"></div>
        </div>

        <div class="image-section" id="imageSection" style="display: none;">
            <div class="image-container">
                <img id="generatedImage" class="generated-image" alt="생성된 이미지">
            </div>

            <div class="description-box" id="descriptionBox">
                <h3>📝 이미지 설명</h3>
                <p id="descriptionText"></p>
            </div>

            <div class="title-suggestion-box" id="titleSuggestionBox" style="display: none;">
                <h3>✨ 추천 제목</h3>
                <p style="color: #666; margin-bottom: 15px;">이미지에 어울리는 제목을 선택하거나 직접 입력하세요:</p>
                <div class="title-suggestions" id="titleSuggestions"></div>
                <div style="margin-top: 15px;">
                    <input type="text" id="customTitleInput" placeholder="또는 직접 제목을 입력하세요" style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 8px;">
                </div>
                <div style="display: flex; gap: 10px; margin-top: 15px;">
                    <button class="btn btn-primary" onclick="selectTitle()">제목 선택</button>
                    <button class="btn btn-secondary" onclick="skipTitleSelection()">건너뛰기</button>
                </div>
            </div>

            <div class="current-title-box" id="currentTitleBox" style="display: none;">
                <h3>📌 현재 제목</h3>
                <p id="currentTitleText" style="font-size: 18px; font-weight: 600; color: #333;"></p>
                <button class="btn btn-secondary" onclick="editTitle()" style="margin-top: 10px;">제목 수정</button>
            </div>

            <div class="action-buttons">
                <button class="btn btn-success" onclick="saveImage()">💾 이미지 저장</button>
                <button class="btn btn-primary" onclick="regenerateImage()">🔄 다시 생성</button>
                <button class="btn btn-secondary" onclick="editText()">✏️ 텍스트 수정</button>
                <button class="btn btn-secondary" onclick="editImageMetadata()">📝 정보 수정</button>
                <button class="btn btn-danger" onclick="deleteCurrentImage()">🗑️ 삭제</button>
            </div>

            <div class="edit-metadata-form" id="editMetadataForm">
                <h3>이미지 정보 수정</h3>
                <label>제목:</label>
                <input type="text" id="editTitleInput" placeholder="이미지 제목을 입력하세요">
                
                <label>태그 (쉼표로 구분 또는 Enter 키로 추가):</label>
                <div style="display: flex; gap: 5px;">
                    <input type="text" id="editTagsInput" placeholder="태그1, 태그2, 태그3" style="flex: 1;">
                    <button class="btn btn-secondary" onclick="addTag()" type="button">추가</button>
                </div>
                <div id="tagsDisplay" class="tags-input"></div>
                
                <label>설명:</label>
                <textarea id="editDescriptionInput" rows="4" placeholder="이미지 설명을 입력하세요"></textarea>
                
                <div style="display: flex; gap: 10px; margin-top: 10px;">
                    <button class="btn btn-primary" onclick="saveImageMetadata()">저장</button>
                    <button class="btn btn-secondary" onclick="cancelEditMetadata()">취소</button>
                </div>
            </div>

            <div class="edit-text-area" id="editTextArea">
                <textarea id="editTextInput" style="margin-top: 10px;"></textarea>
                <button class="btn btn-primary" onclick="updateText()" style="margin-top: 10px;">수정 완료</button>
            </div>
        </div>
    </div>

    <script>
        let currentImageData = null;
        let currentText = '';
        let currentImageId = null;

        // 드래그 앤 드롭 기능
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');

        dropZone.addEventListener('click', () => fileInput.click());

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFile(files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFile(e.target.files[0]);
            }
        });

        // 검색 입력 필드에서 Enter 키 지원
        document.getElementById('searchInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                searchImages();
            }
        });

        async function handleFile(file) {
            const reader = new FileReader();
            reader.onload = async (e) => {
                const textContent = e.target.result;
                document.getElementById('textInput').value = textContent;
                currentText = textContent;
                
                // AI를 통해 이미지화 요약 설명 생성
                await generateImageDescription(textContent);
            };
            reader.readAsText(file);
        }

        async function generateImageDescription(textContent) {
            try {
                const response = await fetch('generate_description.php', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ text: textContent })
                });

                const result = await response.json();
                if (result.success) {
                    document.getElementById('descriptionText').textContent = result.description;
                    document.getElementById('descriptionBox').style.display = 'block';
                }
            } catch (error) {
                console.error('설명 생성 오류:', error);
            }
        }

        async function generateImage() {
            const textInput = document.getElementById('textInput').value.trim();
            
            if (!textInput) {
                showError('텍스트를 입력하거나 파일을 업로드해주세요.');
                return;
            }

            currentText = textInput;
            document.getElementById('loading').style.display = 'block';
            document.getElementById('error').style.display = 'none';
            document.getElementById('imageSection').style.display = 'none';

            try {
                const response = await fetch('generate_image.php', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ text: textInput })
                });

                const result = await response.json();

                if (result.success) {
                    currentImageData = result.imageUrl;
                    currentImageId = result.imageId;
                    currentText = textInput;
                    document.getElementById('generatedImage').src = result.imageUrl;
                    document.getElementById('descriptionText').textContent = result.description || '설명이 생성되었습니다.';
                    document.getElementById('imageSection').style.display = 'block';
                    document.getElementById('descriptionBox').style.display = 'block';
                    
                    // 제목 추천이 있으면 표시
                    if (result.suggestedTitles && result.suggestedTitles.length > 0) {
                        displayTitleSuggestions(result.suggestedTitles);
                    } else {
                        document.getElementById('titleSuggestionBox').style.display = 'none';
                        document.getElementById('currentTitleBox').style.display = 'none';
                    }
                    
                    // 자동 저장 메시지 표시
                    if (result.message && result.message.includes('자동으로 저장')) {
                        setTimeout(() => {
                            alert('✅ 이미지가 생성되고 자동으로 저장되었습니다!');
                        }, 500);
                    }
                } else {
                    // 상세한 에러 메시지 표시
                    let errorMsg = result.message || '이미지 생성에 실패했습니다.';
                    if (result.details) {
                        errorMsg += '\n\n상세 정보: ' + result.details;
                    }
                    showError(errorMsg);
                }
            } catch (error) {
                showError('오류가 발생했습니다: ' + error.message);
            } finally {
                document.getElementById('loading').style.display = 'none';
            }
        }

        async function saveImage() {
            if (!currentImageData) {
                showError('저장할 이미지가 없습니다.');
                return;
            }

            // 저장 중 표시
            const saveButtons = document.querySelectorAll('button[onclick*="saveImage"]');
            const originalTexts = [];
            saveButtons.forEach((btn, index) => {
                originalTexts[index] = btn.textContent;
                btn.disabled = true;
                btn.textContent = '저장 중...';
            });

            try {
                const response = await fetch('save_image.php', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        imageId: currentImageId || null,
                        imageUrl: currentImageData,
                        text: currentText
                    })
                });

                const result = await response.json();

                if (result.success) {
                    if (result.imageId) {
                        currentImageId = result.imageId;
                    }
                    alert('✅ 이미지가 성공적으로 저장되었습니다!');
                } else {
                    showError(result.message || '이미지 저장에 실패했습니다.');
                }
            } catch (error) {
                showError('저장 오류: ' + error.message);
            } finally {
                saveButtons.forEach((btn, index) => {
                    btn.disabled = false;
                    if (originalTexts[index]) {
                        btn.textContent = originalTexts[index];
                    }
                });
            }
        }

        async function regenerateImage() {
            if (!currentImageId) {
                // 이미지 ID가 없으면 일반 생성
                await generateImage();
                return;
            }

            // 기존 이미지가 있으면 업데이트
            const textInput = document.getElementById('textInput').value.trim();
            
            if (!textInput) {
                showError('텍스트를 입력해주세요.');
                return;
            }

            document.getElementById('loading').style.display = 'block';
            document.getElementById('error').style.display = 'none';

            try {
                const response = await fetch('regenerate_and_update.php', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        imageId: currentImageId,
                        text: textInput
                    })
                });

                const result = await response.json();

                if (result.success) {
                    currentImageData = result.imageUrl;
                    currentText = textInput;
                    document.getElementById('generatedImage').src = result.imageUrl;
                    document.getElementById('descriptionText').textContent = result.description || '설명이 생성되었습니다.';
                    document.getElementById('imageSection').style.display = 'block';
                    document.getElementById('descriptionBox').style.display = 'block';
                    alert('이미지가 재생성되었습니다!');
                } else {
                    showError(result.message || '이미지 재생성에 실패했습니다.');
                }
            } catch (error) {
                showError('재생성 오류: ' + error.message);
            } finally {
                document.getElementById('loading').style.display = 'none';
            }
        }

        function editText() {
            const editArea = document.getElementById('editTextArea');
            const editInput = document.getElementById('editTextInput');
            editInput.value = currentText;
            editArea.classList.add('active');
        }

        async function updateText() {
            const newText = document.getElementById('editTextInput').value.trim();
            if (!newText) {
                showError('텍스트를 입력해주세요.');
                return;
            }

            if (!currentImageId) {
                showError('수정할 이미지가 없습니다.');
                return;
            }

            try {
                const response = await fetch('update_text.php', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        imageId: currentImageId,
                        text: newText
                    })
                });

                const result = await response.json();

                if (result.success) {
                    currentText = newText;
                    document.getElementById('textInput').value = newText;
                    document.getElementById('editTextArea').classList.remove('active');
                    alert('텍스트가 성공적으로 수정되었습니다!');
                } else {
                    showError(result.message || '텍스트 수정에 실패했습니다.');
                }
            } catch (error) {
                showError('수정 오류: ' + error.message);
            }
        }

        async function searchImages() {
            const keyword = document.getElementById('searchInput').value.trim();
            if (!keyword) {
                showError('검색 키워드를 입력해주세요.');
                return;
            }

            try {
                const response = await fetch('search.php', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ keyword: keyword })
                });

                const result = await response.json();

                if (result.success) {
                    displaySearchResults(result.results);
                } else {
                    showError(result.message || '검색에 실패했습니다.');
                }
            } catch (error) {
                showError('검색 오류: ' + error.message);
            }
        }

        function displaySearchResults(results) {
            const resultsDiv = document.getElementById('searchResults');
            if (results.length === 0) {
                resultsDiv.innerHTML = '<p>검색 결과가 없습니다.</p>';
                return;
            }

            resultsDiv.innerHTML = results.map(item => `
                <div class="result-item">
                    <h4>${item.filename}</h4>
                    <p>${item.text.substring(0, 100)}...</p>
                    <p style="font-size: 12px; color: #999;">저장일: ${item.saved_at}</p>
                    <button class="btn btn-primary" onclick="loadImage('${item.image_id}')" style="margin-top: 10px;">불러오기</button>
                </div>
            `).join('');
        }

        async function loadImage(imageId) {
            try {
                const response = await fetch('load_image.php', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ imageId: imageId })
                });

                const result = await response.json();

                if (result.success) {
                    currentImageData = result.imageUrl;
                    currentImageId = result.imageId;
                    currentText = result.text;
                    document.getElementById('generatedImage').src = result.imageUrl;
                    document.getElementById('textInput').value = result.text;
                    document.getElementById('descriptionText').textContent = result.description || '';
                    document.getElementById('imageSection').style.display = 'block';
                    document.getElementById('descriptionBox').style.display = 'block';
                    
                    // 제목 표시
                    if (result.title) {
                        document.getElementById('currentTitleBox').style.display = 'block';
                        document.getElementById('currentTitleText').textContent = result.title;
                        document.getElementById('titleSuggestionBox').style.display = 'none';
                    } else {
                        document.getElementById('currentTitleBox').style.display = 'none';
                        document.getElementById('titleSuggestionBox').style.display = 'none';
                    }
                } else {
                    showError(result.message || '이미지 불러오기에 실패했습니다.');
                }
            } catch (error) {
                showError('불러오기 오류: ' + error.message);
            }
        }

        function showError(message) {
            const errorDiv = document.getElementById('error');
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        }

        let selectedTitleIndex = -1;
        let suggestedTitlesList = [];

        // 제목 추천 표시
        function displayTitleSuggestions(titles) {
            suggestedTitlesList = titles;
            selectedTitleIndex = -1;
            
            const suggestionsDiv = document.getElementById('titleSuggestions');
            suggestionsDiv.innerHTML = titles.map((title, index) => `
                <div class="title-suggestion-item" onclick="selectTitleItem(${index})">
                    <span class="title-text">${escapeHtml(title)}</span>
                    <span class="check-icon">✓</span>
                </div>
            `).join('');
            
            document.getElementById('titleSuggestionBox').style.display = 'block';
            document.getElementById('currentTitleBox').style.display = 'none';
            document.getElementById('customTitleInput').value = '';
        }

        // 제목 항목 선택
        function selectTitleItem(index) {
            selectedTitleIndex = index;
            
            // 모든 항목에서 selected 클래스 제거
            document.querySelectorAll('.title-suggestion-item').forEach((item, i) => {
                if (i === index) {
                    item.classList.add('selected');
                } else {
                    item.classList.remove('selected');
                }
            });
            
            // 선택된 제목을 커스텀 입력란에 표시
            document.getElementById('customTitleInput').value = suggestedTitlesList[index];
        }

        // 제목 선택 완료
        async function selectTitle() {
            let selectedTitle = '';
            
            if (selectedTitleIndex >= 0 && selectedTitleIndex < suggestedTitlesList.length) {
                selectedTitle = suggestedTitlesList[selectedTitleIndex];
            } else {
                selectedTitle = document.getElementById('customTitleInput').value.trim();
            }
            
            if (!selectedTitle) {
                showError('제목을 선택하거나 입력해주세요.');
                return;
            }
            
            if (!currentImageId) {
                showError('이미지 ID가 없습니다.');
                return;
            }
            
            try {
                const response = await fetch('update_image_metadata.php', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        imageId: currentImageId,
                        title: selectedTitle
                    })
                });

                const result = await response.json();

                if (result.success) {
                    // 제목 선택 박스 숨기고 현재 제목 박스 표시
                    document.getElementById('titleSuggestionBox').style.display = 'none';
                    document.getElementById('currentTitleBox').style.display = 'block';
                    document.getElementById('currentTitleText').textContent = selectedTitle;
                    alert('✅ 제목이 저장되었습니다!');
                } else {
                    showError(result.message || '제목 저장에 실패했습니다.');
                }
            } catch (error) {
                showError('제목 저장 오류: ' + error.message);
            }
        }

        // 제목 선택 건너뛰기
        function skipTitleSelection() {
            document.getElementById('titleSuggestionBox').style.display = 'none';
            document.getElementById('currentTitleBox').style.display = 'none';
        }

        // 제목 수정
        function editTitle() {
            document.getElementById('titleSuggestionBox').style.display = 'block';
            document.getElementById('currentTitleBox').style.display = 'none';
            
            // 현재 제목을 커스텀 입력란에 표시
            const currentTitle = document.getElementById('currentTitleText').textContent;
            document.getElementById('customTitleInput').value = currentTitle;
            selectedTitleIndex = -1;
            
            // 모든 선택 해제
            document.querySelectorAll('.title-suggestion-item').forEach(item => {
                item.classList.remove('selected');
            });
        }

        // 저장된 이미지 목록 불러오기
        async function loadSavedImages() {
            try {
                // 상대 경로 사용 (index.php와 같은 디렉토리에 있다고 가정)
                let url = 'list_images.php';
                
                // 절대 경로가 필요한 경우를 대비
                if (window.location.pathname.includes('/')) {
                    const pathParts = window.location.pathname.split('/');
                    pathParts.pop(); // index.php 제거
                    const basePath = pathParts.join('/') + '/';
                    url = basePath + 'list_images.php';
                }
                
                console.log('이미지 목록 요청 URL:', url);
                
                const response = await fetch(url, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    cache: 'no-cache'
                });
                
                // 응답이 성공적인지 확인
                if (!response.ok) {
                    const errorText = await response.text();
                    console.error('서버 응답 오류:', response.status, errorText);
                    
                    if (response.status === 404) {
                        // 대체 방법: 직접 search.php를 사용하여 모든 이미지 가져오기
                        console.log('list_images.php를 찾을 수 없습니다. 대체 방법을 시도합니다...');
                        await loadSavedImagesAlternative();
                        return;
                    } else {
                        showError('HTTP 오류: ' + response.status + ' - ' + errorText.substring(0, 100));
                    }
                    return;
                }
                
                // 먼저 텍스트로 받아서 확인
                const text = await response.text();
                console.log('서버 응답:', text.substring(0, 200));
                
                // JSON인지 확인
                let result;
                try {
                    result = JSON.parse(text);
                } catch (parseError) {
                    console.error('JSON 파싱 오류:', parseError, text.substring(0, 200));
                    showError('서버 응답 오류: JSON 형식이 아닙니다. ' + text.substring(0, 100));
                    return;
                }

                if (result.success) {
                    displaySavedImages(result.images || []);
                    document.getElementById('savedImagesSection').style.display = 'block';
                } else {
                    showError(result.message || '이미지 목록을 불러올 수 없습니다.');
                }
            } catch (error) {
                console.error('이미지 목록 불러오기 오류:', error);
                // 대체 방법 시도
                await loadSavedImagesAlternative();
            }
        }

        // 대체 방법: search.php를 사용하여 모든 이미지 가져오기
        async function loadSavedImagesAlternative() {
            try {
                // 빈 키워드로 검색하면 모든 이미지를 가져올 수 있도록 search.php 수정 필요
                // 또는 직접 메타데이터 파일들을 읽는 방법 사용
                showError('list_images.php에 접근할 수 없습니다. 검색 기능을 사용해주세요.');
            } catch (error) {
                showError('이미지 목록을 불러올 수 없습니다: ' + error.message);
            }
        }

        function displaySavedImages(images) {
            const grid = document.getElementById('imagesGrid');
            
            if (images.length === 0) {
                grid.innerHTML = '<p>저장된 이미지가 없습니다.</p>';
                return;
            }

            grid.innerHTML = images.map(image => `
                <div class="image-card">
                    <img src="${image.image_url}" alt="${image.title || image.filename}" onclick="loadImage('${image.image_id}')" style="cursor: pointer;">
                    <div class="image-card-title">${image.title || '제목 없음'}</div>
                    <div class="image-card-text">${image.text.substring(0, 50)}${image.text.length > 50 ? '...' : ''}</div>
                    <div class="image-card-date">${image.saved_at || image.created_at}</div>
                    <div class="image-card-actions">
                        <button class="btn btn-primary" onclick="loadImage('${image.image_id}')">보기</button>
                        <button class="btn btn-secondary" onclick="editImageMetadataById('${image.image_id}')">수정</button>
                        <button class="btn btn-danger" onclick="deleteImage('${image.image_id}')">삭제</button>
                    </div>
                </div>
            `).join('');
        }

        function closeSavedImages() {
            document.getElementById('savedImagesSection').style.display = 'none';
        }

        // 현재 이미지 삭제
        async function deleteCurrentImage() {
            if (!currentImageId) {
                showError('삭제할 이미지가 없습니다.');
                return;
            }

            if (!confirm('정말로 이 이미지를 삭제하시겠습니까?')) {
                return;
            }

            await deleteImage(currentImageId);
        }

        // 이미지 삭제
        async function deleteImage(imageId) {
            try {
                const response = await fetch('delete_image.php', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ imageId: imageId })
                });

                const result = await response.json();

                if (result.success) {
                    alert('이미지가 삭제되었습니다.');
                    if (currentImageId === imageId) {
                        // 현재 보고 있는 이미지라면 섹션 숨기기
                        document.getElementById('imageSection').style.display = 'none';
                        currentImageId = null;
                        currentImageData = null;
                    }
                    // 저장된 이미지 목록 새로고침
                    if (document.getElementById('savedImagesSection').style.display === 'block') {
                        await loadSavedImages();
                    }
                } else {
                    showError(result.message || '이미지 삭제에 실패했습니다.');
                }
            } catch (error) {
                showError('삭제 오류: ' + error.message);
            }
        }

        // 이미지 메타데이터 수정 (현재 이미지)
        function editImageMetadata() {
            if (!currentImageId) {
                showError('수정할 이미지가 없습니다.');
                return;
            }

            // 현재 이미지 정보 불러오기
            loadImageMetadata(currentImageId);
        }

        // 이미지 메타데이터 수정 (ID로)
        async function editImageMetadataById(imageId) {
            await loadImageMetadata(imageId);
        }

        // 이미지 메타데이터 불러오기
        async function loadImageMetadata(imageId) {
            try {
                const response = await fetch('load_image.php', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ imageId: imageId })
                });

                const result = await response.json();

                if (result.success) {
                    // 메타데이터 파일에서 추가 정보 가져오기
                    const metadataResponse = await fetch('get_metadata.php', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ imageId: imageId })
                    });

                    const metadataResult = await metadataResponse.json();
                    const metadata = metadataResult.metadata || {};

                    // 폼에 데이터 채우기
                    document.getElementById('editTitleInput').value = metadata.title || '';
                    document.getElementById('editDescriptionInput').value = result.description || '';
                    
                    // 태그 표시
                    const tags = metadata.tags || [];
                    displayTags(tags);

                    // 폼 표시
                    document.getElementById('editMetadataForm').classList.add('active');
                    document.getElementById('editMetadataForm').dataset.imageId = imageId;
                } else {
                    showError(result.message || '이미지 정보를 불러올 수 없습니다.');
                }
            } catch (error) {
                showError('정보 불러오기 오류: ' + error.message);
            }
        }

        // 태그 표시
        function displayTags(tags) {
            const tagsDisplay = document.getElementById('tagsDisplay');
            tagsDisplay.innerHTML = tags.map(tag => `
                <span class="tag">
                    ${escapeHtml(tag)}
                    <span class="tag-remove" onclick="removeTag('${escapeHtml(tag)}')">×</span>
                </span>
            `).join('');
        }

        // 태그 추가
        function addTag() {
            const tagsInput = document.getElementById('editTagsInput');
            const inputValue = tagsInput.value.trim();
            
            if (!inputValue) {
                return;
            }

            // 쉼표로 구분된 태그들 파싱
            const newTags = inputValue.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0);
            
            const tagsDisplay = document.getElementById('tagsDisplay');
            const existingTags = Array.from(tagsDisplay.querySelectorAll('.tag')).map(el => 
                el.textContent.replace('×', '').trim()
            );
            
            newTags.forEach(tag => {
                if (!existingTags.includes(tag)) {
                    tagsDisplay.innerHTML += `
                        <span class="tag">
                            ${escapeHtml(tag)}
                            <span class="tag-remove" onclick="removeTag('${escapeHtml(tag)}')">×</span>
                        </span>
                    `;
                }
            });
            
            tagsInput.value = '';
        }

        // HTML 이스케이프
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // 태그 제거
        function removeTag(tag) {
            const tagsDisplay = document.getElementById('tagsDisplay');
            const tagElement = Array.from(tagsDisplay.querySelectorAll('.tag')).find(el => 
                el.textContent.replace('×', '').trim() === tag
            );
            if (tagElement) {
                tagElement.remove();
            }
        }

        // 메타데이터 저장
        async function saveImageMetadata() {
            const form = document.getElementById('editMetadataForm');
            const imageId = form.dataset.imageId || currentImageId;

            if (!imageId) {
                showError('이미지 ID가 없습니다.');
                return;
            }

            const title = document.getElementById('editTitleInput').value.trim();
            const description = document.getElementById('editDescriptionInput').value.trim();
            
            // 태그 수집
            const tags = Array.from(document.getElementById('tagsDisplay').querySelectorAll('.tag')).map(el => 
                el.textContent.replace('×', '').trim()
            );

            try {
                const response = await fetch('update_image_metadata.php', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        imageId: imageId,
                        title: title,
                        tags: tags,
                        description: description
                    })
                });

                const result = await response.json();

                if (result.success) {
                    alert('이미지 정보가 수정되었습니다.');
                    cancelEditMetadata();
                    
                    // 현재 이미지라면 설명 업데이트
                    if (currentImageId === imageId && description) {
                        document.getElementById('descriptionText').textContent = description;
                    }
                    
                    // 저장된 이미지 목록 새로고침
                    if (document.getElementById('savedImagesSection').style.display === 'block') {
                        await loadSavedImages();
                    }
                } else {
                    showError(result.message || '정보 수정에 실패했습니다.');
                }
            } catch (error) {
                showError('수정 오류: ' + error.message);
            }
        }

        function cancelEditMetadata() {
            document.getElementById('editMetadataForm').classList.remove('active');
            document.getElementById('editTitleInput').value = '';
            document.getElementById('editDescriptionInput').value = '';
            document.getElementById('editTagsInput').value = '';
            document.getElementById('tagsDisplay').innerHTML = '';
        }

        // 태그 입력 필드에서 Enter 키 처리
        document.addEventListener('DOMContentLoaded', function() {
            const tagsInput = document.getElementById('editTagsInput');
            if (tagsInput) {
                tagsInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        addTag();
                    }
                });
            }
        });
    </script>
</body>
</html>
