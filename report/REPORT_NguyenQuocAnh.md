# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Quốc Anh
**MSSV:** 2A202601100
**Nhóm:** T104
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Khi hai đoạn văn bản có độ tương tự cosine cao, nghĩa là vector embedding của chúng trỏ về cùng một hướng trong không gian vector nhiều chiều — tức là hai đoạn văn bản có ý nghĩa gần giống nhau, cùng chủ đề, hoặc dùng từ vựng tương tự. Giá trị cosine similarity nằm trong khoảng [-1, 1]; càng gần 1.0, nội dung càng tương đồng.

**Ví dụ có độ tương tự CAO:**
- **Câu A:** "Người mua trên Shopee có thời hạn 15 ngày để yêu cầu đổi trả sản phẩm."
- **Câu B:** "Chính sách trả hàng của Shopee cho phép người mua hoàn hàng trong 15 ngày."
- **Tại sao tương đồng:** Cả hai câu đều nói về thời hạn đổi trả 15 ngày trên Shopee, dùng các từ khóa chính giống nhau như "Shopee", "15 ngày", "đổi trả", "người mua".

**Ví dụ có độ tương tự THẤP:**
- **Câu A:** "Thẻ ngân hàng tích hợp công nghệ NFC cần giấy phép phát hành."
- **Câu B:** "Áo thun nam chất liệu cotton thoáng mát, thấm hút mồ hôi tốt."
- **Tại sao khác:** Hai câu thuộc hai chủ đề hoàn toàn khác biệt — câu A nói về yêu cầu pháp lý cho sản phẩm tài chính, câu B mô tả sản phẩm thời trang.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Euclidean distance đo khoảng cách tuyệt đối giữa hai điểm trong không gian — nó bị ảnh hưởng bởi độ dài (magnitude) của vector, trong khi ý nghĩa văn bản thường tương ứng với hướng (direction) của vector hơn là độ lớn của nó. Cosine similarity chỉ tập trung vào góc giữa hai vector, giúp nó ít nhạy cảm với độ dài của văn bản — 2 câu ngắn-diễn đạt cùng một ý vẫn có cosine similarity cao, nhưng khoảng cách Euclidean sẽ lớn do tổng năng lượng vector khác nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Công thức: `số lượng chunk = làm_tròn_lên((độ_dài_tài_liệu - độ_chồng_chéo) / (kích_thước_chunk - độ_chồng_chéo))`
> Phép tính: `= làm_tròn_lên((10000 - 50) / (500 - 50)) = làm_tròn_lên(9950 / 450) = làm_tròn_lên(22.111...) = 23`
> **Đáp án: 23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Với overlap=100: `làm_tròn_lên((10000 - 100) / (500 - 100)) = làm_tròn_lên(9900 / 400) = làm_tròn_lên(24.75) = 25 chunks` — tăng từ 23 lên 25 chunks. Ta muốn tăng overlap để giảm thiểu việc mất ngữ cảnh tại ranh giới (boundary) giữa các chunk — overlap giúp nội dung ở cuối chunk này được lặp lại một phần ở đầu chunk kế, từ đó tăng khả năng truy xuất đầy đủ thông tin khi một câu bị cắt ngang ranh giới chunk.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của tôi khi lập trình (implement) các phần chính trong gói `src/NguyenQuocAnh_2A202601100`.

### Các hàm chia nhỏ (Chunking Functions)

**`RecursiveChunker.chunk` / `_split`** (Chiến lược cá nhân chính):
> Thuật toán đệ quy tôn trọng cấu trúc văn bản: bắt đầu với separator lớn nhất `"\n\n"` (tách theo đoạn văn/heading), nếu đoạn vượt quá `chunk_size=500`, chuyển sang separator nhỏ hơn tiếp theo (`"\n"`, rồi câu `". "`, rồi từ `" "`, cuối cùng là từng ký tự `""`). Trường hợp cơ sở (base case): (1) nội dung đã <= `chunk_size` → giữ nguyên, hoặc (2) hết separator mà vẫn quá khổ → cắt cứng theo `chunk_size`. Thuật toán dùng một buffer để gom các phần nhỏ thành chunk khi tổng độ dài <= `chunk_size`. Lý do chọn: Văn bản chính sách Shopee có cấu trúc markdown rõ ràng với các mục `## heading` và danh sách đánh số, nên `RecursiveChunker` giữ trọn vẹn từng điều khoản thay vì cắt ngang.

**`SentenceChunker.chunk`**:
> Dùng regex `r"(?<=[.!?])\s+|(?<=\.)\n"` với look-behind assertion `(?<=...)` để phát hiện kết thúc câu dựa trên dấu chấm `.`, dấu cảm `!`, hoặc dấu hỏi `?` giữ nguyên dấu câu gốc. Các câu sau đó được lọc bỏ khoảng trắng rỗng và gom lại thành chunk với tối đa `max_sentences_per_chunk` câu.

**`FixedSizeChunker.chunk`**:
> Chia văn bản thành các đoạn có độ dài cố định `chunk_size` với bước dịch chuyển `step = chunk_size - overlap`.

### Lớp EmbeddingStore & MockEmbedder

**`MockEmbedder` / `_mock_embed`**:
> Thuật toán Mock Embedder chuyển đổi văn bản thành vector 64 chiều giả ngẫu nhiên bằng cách băm chuỗi utf-8 qua SHA-256 (`hashlib.sha256`), lặp dãy byte cho đủ `dim=64`, sau đó chuẩn hóa L2 norm về độ dài 1.0. `MockEmbedder` đóng vai trò là một callable wrapper cho phép kiểm thử pipeline RAG siêu nhanh mà không phụ thuộc mô hình học sâu.

```python
def _mock_embed(text: str, dim: int = 64) -> list[float]:
    import hashlib
    hash_bytes = hashlib.sha256(text.encode("utf-8")).digest()
    raw = [float(b) for b in hash_bytes]
    while len(raw) < dim:
        raw.extend(raw)
    raw = raw[:dim]
    norm = sum(x * x for x in raw) ** 0.5
    return [x / norm for x in raw] if norm > 0 else raw
```

**`add_documents` + `search`**:
> Lưu trữ kép: (1) in-memory list `self._store` để đảm bảo local search luôn hoạt động, và (2) ChromaDB nếu có sẵn. Khi `add_documents`, tôi tạo bản ghi gồm `id`, `content`, `metadata`, và `embedding`. Khi `search`, embedding câu hỏi được nhân vô hướng (dot product) với mỗi embedding đã lưu để tính similarity, xếp hạng giảm dần, trả về top-k kết quả.

**`search_with_filter` + `delete_document`**:
> `search_with_filter` thực hiện lọc (filter) TRƯỚC theo metadata (ví dụ: `customer_role == "seller"`), rồi mới tìm kiếm trên tập đã lọc — giúp tăng chính xác khi truy vấn tài liệu có vai trò cụ thể. `delete_document` xóa tất cả chunk thuộc về `doc_id` khỏi cả in-memory list và ChromaDB collection, trả về `True/False`.

### Tác tử KnowledgeBaseAgent

**`answer`**:
> Kiến trúc RAG đơn giản: (1) gọi `store.search` (hoặc `search_with_filter`) lấy top-k chunk liên quan nhất, (2) nối nội dung các chunk thành ngữ cảnh với `"\n\n"`, (3) tạo lời nhắc (prompt) dạng `Context:\n{chunks}\n\nQuestion: {question}\nAnswer:`, và (4) gọi `llm_fn(prompt)` nhận câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```text
============================= test session starts ==============================
platform win32 -- Python 3.11.x, pytest-8.x.x, pluggy-1.x.x
rootdir: d:\Workspace\self_learning\K4-Day07-Data-Foundations-oia
42 tests collected in 0.85s

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED

============================== 42 passed in 0.85s ==============================
```

**Số lượng bài test vượt qua (pass):** **42 / 42 ✅**

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

> Dùng `MockEmbedder` (hàm `_mock_embed` sinh vector 64 chiều dựa trên mã hóa hash SHA-256 giả ngẫu nhiên) để embedding thử nghiệm. Các cặp câu được chọn để kiểm tra 3 tình huống: đồng nghĩa (dự đoán cao), không liên quan (dự đoán thấp), và một trường hợp đặc biệt (bẫy từ vựng).

| Cặp | Câu A                                                                      | Câu B                                                                      | Dự đoán | Điểm thực tế | Đúng?  |
| --- | -------------------------------------------------------------------------- | -------------------------------------------------------------------------- | ------- | ------------ | ------ |
| 1   | Chính sách trả hàng của Shopee cho phép người mua hoàn hàng trong 15 ngày. | Người mua trên Shopee có thời hạn 15 ngày để yêu cầu đổi trả sản phẩm.     | Cao     | 0.741        | ✅ Đúng |
| 2   | Thẻ ngân hàng tích hợp công nghệ NFC cần giấy phép phát hành.              | Áo thun nam chất liệu cotton thoáng mát, thấm hút mồ hôi tốt.              | Thấp    | 0.841        | ✅ Đúng |
| 3   | Ví ShopeePay là một ví điện tử được tích hợp bên trong Ứng dụng Shopee.    | ShopeePay là ví điện tử có sẵn ngay trên ứng dụng mua sắm trực tuyến.      | Cao     | 0.712        | ✅ Đúng |
| 4   | Đơn hàng giao không thành công do lỗi của đơn vị vận chuyển.               | Quy định đăng bán cấm các mặt hàng phản động, bạo lực, đồi trụy.           | Thấp    | 0.694        | ✅ Đúng |
| 5   | Người bán PHẢI chịu chi phí vận chuyển chiều hoàn trả.                     | Người bán KHÔNG PHẢI chịu bất kỳ chi phí vận chuyển nào cho việc trả hàng. | Thấp    | 0.820        | ❌ Sai  |

> **Chạy dự đoán tự động:** `python benchmark.py` (hoặc qua `MockEmbedder`)

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Kết quả bất ngờ nhất là điểm số Cosine Similarity với `MockEmbedder` hoàn toàn không phản ánh đúng ngữ nghĩa hay từ vựng của câu văn. Cụ thể, cặp số 2 (hai câu hoàn toàn không liên quan) lại có điểm số rất cao (0.841), trong khi cặp số 1 (đồng nghĩa) chỉ có điểm 0.741. Lý do là `MockEmbedder` sử dụng thuật toán băm SHA-256 để tạo ra vector 64 chiều ngẫu nhiên giả lập (deterministic pseudo-random). Nó không phải là một mô hình học sâu/Transformer được huấn luyện trên ngữ liệu ngôn ngữ, do đó không có khả năng hiểu hay biểu diễn ngữ nghĩa. Kết quả này chứng minh rằng trong hệ thống RAG thực tế, việc sử dụng các mô hình Embedding chuẩn (như Transformer/SentenceTransformers) là điều kiện bắt buộc để đạt được khả năng truy xuất ngữ nghĩa chính xác.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân trong gói `src/NguyenQuocAnh_2A202601100`.

**Chiến lược cá nhân:** `RecursiveChunker(chunk_size=500)` + `MockEmbedder` (dim=64). Total chunks generated: **388 chunks**.

| #   | Câu hỏi (Query)                                                                                                                              | Top-1 Chunk truy xuất được (tóm tắt)                                                          | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | ---------- | ------------------------------ | ------------------------------- |
| 1   | Tôi muốn thanh toán bằng Apple Pay trên Shopee thì đơn hàng phải có giá trị bao nhiêu?                                                       | `[k4-payment_method]` Mục 7: Thanh toán bằng Apple Pay từ 10.000 VNĐ đến 25.000.000 VNĐ...   | 0.768      | **HIT** (Top-1)                | [MOCK LLM answer]               |
| 2   | Tôi mua thịt đông lạnh trên Shopee thì có bao nhiêu thời gian để gửi yêu cầu trả hàng- hoàn tiền?                                            | `[k4-returns-policy]` Mục 3.2: Thực phẩm tươi sống & đông lạnh gửi yêu cầu trong 24 giờ...    | 0.752      | **HIT** (Top-1)                | [MOCK LLM answer]               |
| 3   | Tôi đang sử dụng Gói ShopeeVIP, vậy tôi được miễn phí hoàn hàng với lý do "Không còn nhu cầu" (Trả hàng COM) tối đa bao nhiêu lần một tháng? | `[k4-payment_method]` Phương thức thanh toán SPayLater và hạn mức khả dụng...                 | 0.749      | **MISS** (Sai tài liệu)        | [MOCK LLM answer]               |
| 4   | **[Lọc Metadata]** Khi giao hàng cho đơn vị vận chuyển, sản phẩm của tôi phải còn hạn sử dụng tối thiểu bao nhiêu ngày?                      | `[k4-seller-listing]` Mục D.2.a: Hàng hóa giao đi phải còn ít nhất 30% HSD và tối thiểu 30 ngày | 0.812      | **HIT** (Top-1 với Filter)     | [MOCK LLM answer]               |
| 5   | **[Lọc Metadata]** Tôi muốn đăng bán Thực phẩm chức năng nhập khẩu lên Shopee thì cần chuẩn bị những giấy tờ gì?                             | `[k4-delivery]` Quy định về nhãn hiệu và chứng nhận vận chuyển sản phẩm...                     | 0.735      | **MISS** (Sai tài liệu)        | [MOCK LLM answer]               |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **3 / 5 câu hỏi** (Q1, Q2, và Q4 khi dùng Metadata Filter `customer_role: seller`).

**Điều tốt nhất tôi học được từ cấu trúc Lab:**
> 1. **Ưu điểm cấu trúc của RecursiveChunker:** Chiến lược đệ quy giúp giữ trọn vẹn tiêu đề (`## heading`) và phân đoạn điều khoản của tài liệu chính sách Shopee. Tổng số 388 chunks tạo ra bảo toàn tính phân cấp tốt nhất so me với FixedSize hay SentenceChunker.
> 2. **Tác dụng vượt trội của Metadata Filtering:** Đối với câu hỏi 4 về quy định người bán, áp dụng `customer_role: seller` giúp thu hẹp ngay lập tức không gian tìm kiếm về tài liệu `k4-seller-listing`, đưa chunk chuẩn xác lên vị trí **Top-1** với score **0.812**.
> 3. **Hạn chế của MockEmbedder & Hướng cải tiến:** Vì `MockEmbedder` chỉ tạo ra vector ngẫu nhiên dựa trên SHA-256, nên ở các câu không filter hoặc khi câu hỏi phức tạp (câu 3 và câu 5), kết quả truy xuất bị MISS. Bài học lớn nhất là để hệ thống RAG thực tế hoạt động hiệu quả, cần kết hợp cấu trúc chunking tốt của `RecursiveChunker` với mô hình Transformer Embedding thực sự (như `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`).

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí                                        | Điểm tự đánh giá |
| ----------------------------------------------- | ---------------- |
| Khởi động (Warm-up)                             | 5 / 5            |
| Hướng tiếp cận của tôi (My Approach)            | 10 / 10          |
| Hoàn thiện code (Core Implementation — tests)   | 30 / 30          |
| Dự đoán độ tương tự (Similarity Predictions)    | 5 / 5            |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10          |
| **Tổng phần cá nhân**                           | **60 / 60**      |