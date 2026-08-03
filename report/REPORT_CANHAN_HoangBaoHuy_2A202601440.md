# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Hoàng Bảo Huy
**Mã sinh viên:** 2A202601440
**Lớp / Nhóm:** K4 / T104
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao (gần bằng 1.0) thể hiện rằng hai vector nhúng của văn bản có cùng hướng trong không gian ngữ nghĩa nhiều chiều. Điều này chứng tỏ hai đoạn văn bản có sự đồng nhất cao về nội dung hoặc ý nghĩa ngữ cảnh, độc lập với độ dài của câu.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Chính sách đổi trả hàng và hoàn tiền dành cho người mua trên Shopee."
- Câu B: "Hướng dẫn thực hiện yêu cầu hoàn tiền và trả sản phẩm dành cho khách hàng Shopee."
- Tại sao tương đồng: Cả hai câu đều nói về quy trình, quyền lợi đổi trả và hoàn tiền của người mua hàng trên sàn thương mại điện tử Shopee.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Chính sách đổi trả hàng và hoàn tiền dành cho người mua trên Shopee."
- Câu B: "Mô hình mạng thần kinh nhân tạo học sâu trong xử lý hình ảnh."
- Tại sao khác: Câu A thuộc chủ đề dịch vụ khách hàng thương mại điện tử, còn Câu B thuộc lĩnh vực trí tuệ nhân tạo và học máy.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Khoảng cách Euclid bị ảnh hưởng trực tiếp bởi độ dài của văn bản (độ lớn/chuẩn của vector). Hai văn bản có cùng chủ đề nhưng một đoạn dài và một đoạn ngắn sẽ có khoảng cách Euclid rất lớn. Cosine similarity loại bỏ ảnh hưởng của độ dài bằng cách chuẩn hóa vector về độ dài bằng 1 và chỉ đo góc giữa hai vector, giúp đánh giá chính xác độ tương đồng ngữ nghĩa.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> - Kích thước bước dịch (step) giữa hai chunk liên tiếp: $D = \text{chunk\_size} - \text{overlap} = 500 - 50 = 450$ ký tự.
> - Ký tự bắt đầu của các chunk lần lượt là: $0, 450, 900, 1350, \dots, 9900$.
> - Phép tính tổng số chunk: $1 + \lceil (10000 - 500) / 450 \rceil = 1 + \lceil 9500 / 450 \rceil = 1 + \lceil 21.11 \rceil = 1 + 22 = 23$ chunks.
> *Đáp án:* **23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> - Khi overlap = 100, bước dịch $D = 500 - 100 = 400$ ký tự. Số chunk tạo ra là: $1 + \lceil 9500 / 400 \rceil = 1 + 24 = 25$ chunks.
> - Số lượng chunk tăng từ 23 lên **25 chunks**.
> - Ta muốn độ chồng chéo nhiều hơn để đảm bảo ngữ cảnh ở ranh giới giữa các chunk không bị cắt đứt nửa chừng. Việc giữ lại ngữ cảnh liên tục giúp mô hình RAG truy xuất chính xác các ý nằm ở vị trí giao giữa 2 đoạn.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng biểu thức chính quy (regex) `re.split(r"(?<=[.!?])\s+|(?<=\.)\n", text)` để phân tách các câu dựa trên ranh giới câu (`. `, `! `, `? `, `.\n`) mà không làm mất dấu câu cuối câu. Xử lý các edge case như văn bản rỗng, khoảng trắng dư thừa, và gộp tối đa `max_sentences_per_chunk` câu liên tiếp thành từng chunk chuẩn.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Sử dụng giải thuật phân tách đệ quy thử nghiệm danh sách phân cách theo thứ tự ưu tiên `["\n\n", "\n", ". ", " ", ""]`. Base case là khi văn bản ngắn hơn `chunk_size` hoặc đã hết dấu phân cách (chuyển sang cắt theo độ dài ký tự). Hàm gộp các đoạn nhỏ thành chunk lớn tối đa không vượt quá `chunk_size`.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Hàm `add_documents` nhúng từng document bằng `self._embedding_fn` và lưu thành record phẳng chứa `id`, `content`, `metadata`, `embedding`. Tích hợp ChromaDB collection nếu khả dụng, đồng thời giữ bộ lưu trữ trong bộ nhớ (in-memory). Hàm `search` tính tích vô hướng (`_dot`) giữa vector query và tất cả record, sắp xếp giảm dần theo score và lấy top_k kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` thực hiện lọc tiền xử lý (pre-filtering) các record có metadata thỏa mãn tất cả các cặp khóa-giá trị trong `metadata_filter` trước khi tính điểm tương đồng vector. `delete_document` tìm và loại bỏ tất cả các record có `metadata['doc_id']` hoặc `id` trùng khớp với `doc_id` cần xóa, đồng thời cập nhật ChromaDB collection.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Gọi `store.search` để lấy `top_k` chunk liên quan nhất với câu hỏi. Nối nội dung các chunk thành chuỗi ngữ cảnh `context`, sau đó đóng gói thành prompt có cấu trúc `Context: ... Question: ... Answer:` truyền vào `llm_fn` để sinh câu trả lời RAG hoàn chỉnh.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.12.7, pytest-7.4.4, pluggy-1.0.0
rootdir: C:\Users\LEGION 5\.gemini\antigravity\scratch\K4-Day07-Data-Foundations-oia
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.05s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Hàng điện tử bảo hành bao lâu? | Thời gian bảo hành thiết bị điện tử là bao nhiêu? | cao | 0.8201 | Có |
| 2 | Chính sách đổi trả hàng shopee | Cách đăng ký tài khoản bán hàng shopee | thấp | 0.6328 | Có |
| 3 | Đơn hàng Apple Pay tối thiểu bao nhiêu? | Apple Pay áp dụng cho đơn hàng từ 10.000 VNĐ trở lên. | cao | 0.6866 | Có |
| 4 | Trẻ em dưới 13 tuổi có được dùng dịch vụ không? | Món ăn giao hàng nhanh trong 30 phút. | thấp | 0.7680 | Không |
| 5 | Quy định về thời hạn sử dụng sản phẩm khi giao | Sản phẩm giao đi phải còn ít nhất 30% hạn sử dụng. | cao | 0.7637 | Có |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Ở Cặp 4, hai câu hoàn toàn khác ngữ nghĩa nhưng `_mock_embed` lại sinh ra điểm tương đồng khá cao (0.7680). Điều này cho thấy mock embedder dựa trên thuật toán băm (hash) chỉ tạo vector giả lập độc lập với ý nghĩa ngôn ngữ thực tế; do đó trong Giai đoạn 2 cần dùng `LocalEmbedder` (sentence-transformers) hoặc `OpenAIEmbedder` để thu được biểu diễn ngữ nghĩa chính xác.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src/HoangBaoHuy_2A202601440` với dữ liệu `data/k4_ecommerce/`.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Tôi muốn thanh toán bằng Apple Pay trên Shopee thì đơn hàng phải có giá trị bao nhiêu? | Đơn hàng áp dụng Apple Pay từ 10.000 VNĐ đến 25.000.000 VNĐ (`customer_role: buyer`) | 0.8336 | Có | Đơn hàng thanh toán bằng Apple Pay có giá trị từ 10.000 VNĐ đến 25.000.000 VNĐ. |
| 2 | Tôi mua thịt đông lạnh trên Shopee thì có bao nhiêu thời gian để gửi yêu cầu trả hàng hoàn tiền? | Thời gian yêu cầu trả hàng thực phẩm tươi sống/đông lạnh trong vòng 24 giờ (`customer_role: buyer`) | 0.8673 | Có | Thời gian gửi yêu cầu hoàn tiền cho thực phẩm đông lạnh là 24 giờ kể từ khi giao thành công. |
| 3 | Tôi đang sử dụng Gói ShopeeVIP, vậy tôi được miễn phí hoàn hàng với lý do "Không còn nhu cầu" tối đa bao nhiêu lần một tháng? | Hạn mức Trả hàng COM với gói ShopeeVIP là 15 lần/tháng dương lịch (`customer_role: buyer`) | 0.8533 | Có | Người dùng ShopeeVIP được miễn phí hoàn hàng lý do không còn nhu cầu tối đa 15 lần/tháng. |
| 4 | Khi giao hàng cho đơn vị vận chuyển, sản phẩm của tôi phải còn hạn sử dụng tối thiểu bao nhiêu ngày? | Sản phẩm giao đi phải còn ít nhất 30% thời hạn sử dụng và tối thiểu 30 ngày (`customer_role: seller`) | 0.8833 | Có | Hạn sử dụng còn lại tối thiểu là 30 ngày và đạt ít nhất 30% thời hạn sử dụng. |
| 5 | Tôi muốn đăng bán Thực phẩm chức năng nhập khẩu trên Shopee thì cần chuẩn bị những giấy tờ gì? | Hồ sơ gồm Giấy xác nhận công bố phù hợp ATTP, chứng nhận đại lý/hóa đơn, giấy xác nhận quảng cáo (`customer_role: seller`) | 0.8604 | Có | Cần chuẩn bị Giấy công bố ATTP, chứng từ đại lý/hóa đơn và Giấy xác nhận nội dung quảng cáo. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Việc áp dụng tiền lọc siêu dữ liệu (`search_with_filter` dựa trên `customer_role` là `buyer` hoặc `seller`) giúp thu hẹp chính xác phạm vi tìm kiếm, loại bỏ nhiễu giữa quy định dành cho người mua và quy định dành cho người bán, từ đó nâng cao vượt trội độ chính xác của câu trả lời từ RAG Agent.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
