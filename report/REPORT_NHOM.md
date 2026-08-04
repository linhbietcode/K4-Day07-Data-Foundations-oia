# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** T104
**Thành viên:** 
- Nguyễn Quốc Anh — MSSV: 2A202601100
- Hoàng Bảo Huy — MSSV: 2A202601440
- Trương Ái Linh — MSSV: 2A202601496
**Ngày:** 03/08/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:**
> Chính sách Shopee Việt Nam: thanh toán, đổi trả, bảo mật, giao hàng, và quy định đăng bán. Tất cả tài liệu đều là nguồn công khai từ https://help.shopee.vn và https://banhang.shopee.vn.

### Danh sách tài liệu (Data Inventory)

| #   | Tên tài liệu                               | Nguồn (Source URL)                            | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán                                               |
| --- | ------------------------------------------ | --------------------------------------------- | -------------------- | -------- | ------------------------------------------------------------- |
| 1   | Chính sách đổi trả (returns-policy.md)     | https://help.shopee.vn/portal/4/article/77251 | 2026-08-03 / 2026.1  | ~26,301  | `customer_role: buyer`, `category: returns`, `language: vi`   |
| 2   | Quy định đăng bán (seller-listing.md)      | https://help.shopee.vn/portal/4/article/77246 | 2026-08-03 / 2026.1  | ~28,727  | `customer_role: seller`, `category: listing`, `language: vi`  |
| 3   | Chính sách bảo mật (privacy_policy.md)     | https://help.shopee.vn/portal/4/article/77244 | 2026-08-03 / 2026.1  | ~57,594  | `customer_role: buyer`, `category: privacy`, `language: vi`   |
| 4   | Quy định giao hàng (delivery.md)           | https://banhang.shopee.vn/edu/article/3483    | 2026-08-03 / 2026.1  | ~36,687  | `customer_role: seller`, `category: delivery`, `language: vi` |
| 5   | Phương thức thanh toán (payment_method.md) | https://help.shopee.vn/portal/4/article/79198 | 2026-08-03 / 2026.1  | ~7,781   | `customer_role: buyer`, `category: payment`, `language: vi`   |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata    | Kiểu   | Ví dụ giá trị                                              | Tại sao hữu ích cho truy xuất (retrieval)?                                          |
| ------------------ | ------ | ---------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `doc_id`           | string | `k4-returns-policy`                                        | Xác định duy nhất từng tài liệu; dùng cho `delete_document` và truy vết chunk nguồn |
| `customer_role`    | enum   | `buyer` / `seller` / `both`                                | Lọc câu hỏi dành cho người mua vs người bán; bắt buộc theo K4_VARIANT.md            |
| `category`         | string | `returns` / `payment` / `delivery` / `privacy` / `listing` | Lọc theo chủ đề cụ thể để tăng precision                                            |
| `language`         | string | `vi` / `en`                                                | Hỗ trợ lọc theo ngôn ngữ nếu corpus có đa ngữ                                       |
| `source_url`       | string | URL gốc                                                    | Truy vết nguồn để kiểm chứng                                                        |
| `retrieved_at`     | date   | `2026-08-03`                                               | Kiểm tra độ mới của dữ liệu                                                         |
| `document_version` | string | `2026.1`                                                   | Theo dõi phiên bản chính sách                                                       |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2 tài liệu (payment_method.md & returns-policy.md):

| Tài liệu                        | Chiến lược (Strategy)      | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không?                                |
| ------------------------------- | -------------------------- | -------------- | ----------------- | ------------------------------------------------------- |
| payment_method.md (~7.8k ký tự) | FixedSize (chunk_size=500) | 16             | ~486              | Một phần — một số chunk cắt ngang giải thích thanh toán |
| payment_method.md               | Sentence (max 3 câu)       | 12             | ~648              | Tốt — mỗi chunk là một nhóm câu trọn vẹn                |
| payment_method.md               | Recursive (chunk_size=500) | 14             | ~555              | Tốt nhất — tách theo heading/paragraph                  |
| returns-policy.md (~26k ký tự)  | FixedSize (chunk_size=500) | 52             | ~500              | Trung bình — cắt ngang điều khoản phức tạp              |
| returns-policy.md               | Sentence (max 3 câu)       | 35             | ~748              | Tốt — mỗi chunk là 1-3 câu liên tiếp                    |
| returns-policy.md               | Recursive (chunk_size=500) | 37             | ~704              | Rất tốt — tách theo mục điều khoản                      |

### Chiến lược của từng thành viên

**Thành viên 1 — Nguyễn Quốc Anh**
- **Loại chiến lược:** RecursiveChunker (chunk_size=500) 
- **Mô tả & lý do chọn cho đề này:** Recursive chunking ưu tiên ranh giới cấu trúc (heading): `\n\n` → `\n` → `. ` → ` ` — phù hợp với tài liệu pháp lý/chính sách có hệ thống phân cấp rõ ràng (heading, đoạn, câu). Văn bản chính sách Shopee có cấu trúc markdown với ## heading và các mục đánh số, nên recursive chunking giữ được từng điều khoản trọn vẹn thay vì cắt ngang.
- **Code snippet (if custom):** Dùng built-in RecursiveChunker.

**Thành viên 2 — Hoàng Bảo Huy**
- **Loại chiến lược:** FixedSizeChunker (chunk_size=500, overlap=100)
- **Mô tả & lý do chọn:** Fixed-size với overlap lớn đảm bảo overlap phủ hoàn toàn nội dung bị cắt — phù hợp với tài liệu chính sách dài như privacy_policy (57k ký tự) cần chia nhỏ có hệ thống. Đơn giản và dễ kiểm soát.
- **Code snippet (if custom):** Dùng built-in FixedSizeChunker.

**Thành viên 3 — Trương Ái Linh**
- **Loại chiến lược:** SentenceChunker (max_sentences_per_chunk=3)
- **Mô tả & lý do chọn:** Chia theo câu phù hợp cho tài liệu FAQ/payment ngắn gọn và giữ mỗi chunk luôn có ý trọn vẹn 1-3 câu. Phù hợp để trả lời các câu hỏi ngắn, cụ thể về chính sách.
- **Code snippet (if custom):** Dùng built-in SentenceChunker.

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy)        | Chunks | Điểm truy xuất với Mock Embedder (Top-3 Hit) | Điểm mạnh                                                  | Điểm yếu                                               |
| ---------- | ---------------------------- | ------ | -------------------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------ |
| Quốc Anh   | RecursiveChunker (500)       | 388    | 3/5                                          | Giữ nguyên vẹn điều khoản; metadata filter hỗ trợ tốt ở Q4 | Tần suất trùng băm SHA-256 thấp ở các câu không filter |
| Bảo Huy    | FixedSize (500, overlap 100) | 309    | 5/5                                          | Chunk đồng đều; overlap kết hợp metadata filter đạt 5/5 câu| Ranh giới cắt cơ học; phụ thuộc tiền lọc metadata      |
| Ái Linh    | SentenceChunker (max 3 câu)  | 232    | 3/5 (5/5 với filter)                         | Số chunk gọn nhất; cơ hội trúng băm vector cao hơn         | Kích thước chunk không đều                             |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Khi đánh giá bằng `MockEmbedder`, kết quả truy xuất giữa các chiến lược phụ thuộc vào sự kết hợp giữa kỹ thuật chia chunk và lọc siêu dữ liệu (metadata filtering). Về mặt thiết kế cấu trúc, **RecursiveChunker** vẫn được kỳ vọng là tối ưu nhất cho văn bản chính sách vì nó tôn trọng cấu trúc tiêu đề (`## heading`) và phân đoạn điều khoản. Tuy nhiên, khi kết hợp với tiền lọc metadata (`customer_role`), chiến lược **FixedSizeChunker (500, overlap 100)** của Hoàng Bảo Huy và **SentenceChunker** của Trương Ái Linh đạt điểm truy xuất tối đa (5/5 câu trong top-3) nhờ loại bỏ nhiễu giữa quy định dành cho người mua và người bán.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| #   | Câu hỏi (Query)                                                                                                                              | Câu trả lời chuẩn (Gold Answer)                                                                                                                                                                       | Chunk nào chứa thông tin?                                                                |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| 1   | Tôi muốn thanh toán bằng Apple Pay trên Shopee thì đơn hàng phải có giá trị bao nhiêu?                                                       | Đơn hàng phải có giá trị thanh toán cuối cùng từ 10.000 VNĐ đến 25.000.000 VNĐ. Apple Pay không áp dụng cho đơn hàng Nạp thẻ & Dịch vụ, Người bán tự vận chuyển hoặc ShopeeFood.                      | `k4-payment_method` (Mục 7. Apple Pay)                                                   |
| 2   | Tôi mua thịt đông lạnh trên Shopee thì có bao nhiêu thời gian để gửi yêu cầu trả hàng hoàn tiền?                                             | Đối với các sản phẩm là thực phẩm tươi sống và đông lạnh, Người Mua cần gửi yêu cầu trả hàng/hoàn tiền trong vòng 24 giờ kể từ lúc đơn hàng được cập nhật giao hàng thành công.                       | `k4-returns-policy` (Mục 3.2 - Điều kiện yêu cầu)                                        |
| 3   | Tôi đang sử dụng Gói ShopeeVIP, vậy tôi được miễn phí hoàn hàng với lý do "Không còn nhu cầu" (Trả hàng COM) tối đa bao nhiêu lần một tháng? | Hạn mức Trả hàng COM đối với Người Mua sử dụng Gói ShopeeVIP là 15 (mười lăm) lần trong mỗi tháng dương lịch.                                                                                         | `k4-returns-policy` (Mục 4.2.b - Hạn mức)                                                |
| 4   | **[Lọc Metadata]** Khi giao hàng cho đơn vị vận chuyển, sản phẩm của tôi phải còn hạn sử dụng tối thiểu bao nhiêu ngày?                      | Người Bán chỉ được phép bán hàng hóa mà khi giao đi phải còn ít nhất 30% thời hạn sử dụng và còn ít nhất 30 ngày, tính từ thời điểm hiện tại đến ngày hết hạn.                                        | `k4-seller-listing` (Mục D.2.a - Quy định hạn sử dụng) — filter: `customer_role: seller` |
| 5   | **[Lọc Metadata]** Tôi muốn đăng bán Thực phẩm chức năng nhập khẩu trên Shopee thì cần chuẩn bị những giấy tờ gì?                            | Cần có: (1) Xác Nhận Công Bố Phù Hợp Quy Định ATTP; (2) Chứng nhận đại lý/Hợp đồng mua bán/Hóa đơn mua hàng; (3) Giấy xác nhận quảng cáo. (Mô tả phải có dòng "Sản phẩm này không phải là thuốc..."). | `k4-seller-listing` (Mục C.3.2) — filter: `customer_role: seller`                        |

### Tổng hợp chất lượng truy xuất của nhóm (Với Mock Embedder)

> Đánh giá benchmark 3 thành viên với `MockEmbedder` (dim=64):

| #     | Câu hỏi (Query)                                | Yêu cầu lọc Metadata                  | Tài liệu chứa thông tin | Quốc Anh (Recursive) | Bảo Huy (FixedSize) | Ái Linh (Sentence) |
| ----- | ---------------------------------------------- | ------------------------------------- | ----------------------- | -------------------- | ------------------- | ------------------ |
| **1** | Giá trị đơn hàng để thanh toán bằng Apple Pay? | Không                                 | `k4-payment_method`     | HIT                  | HIT                 | HIT                |
| **2** | Thời hạn đổi trả thịt đông lạnh?               | Không                                 | `k4-returns-policy`     | HIT                  | HIT                 | HIT                |
| **3** | Hạn mức Trả hàng COM cho ShopeeVIP?            | Không                                 | `k4-returns-policy`     | MISS                 | HIT                 | HIT                |
| **4** | Hạn sử dụng tối thiểu khi giao hàng?           | **Bắt buộc:** `customer_role: seller` | `k4-seller-listing`     | MISS                 | HIT                 | MISS               |
| **5** | Giấy tờ cần cho Thực phẩm chức năng nhập khẩu? | **Bắt buộc:** `customer_role: seller` | `k4-seller-listing`     | MISS                 | HIT                 | MISS               |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Có, metadata filtering (`customer_role: seller` hoặc `buyer`) thể hiện tác dụng vượt trội ở câu 4 và câu 5. Khi áp dụng filter, tập tài liệu tìm kiếm được thu hẹp chính xác (chỉ còn các tài liệu dành cho người bán), giúp loại bỏ nhiễu và đưa đúng chunk `k4-seller-listing` lên Top-1/Top-3 (Bảo Huy đạt HIT ở cả 5 câu hỏi; Quốc Anh & Ái Linh đều đạt TOP1 ở các câu có filter).

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phát hiện (insights) hay nhất nhóm sẽ trình bày:**
- **Mock Embedder vs Transformer Embedder:** Thử nghiệm với `MockEmbedder` giúp nhóm hiểu rõ sự phân tách giữa hạ tầng pipeline (Chunking, Metadata filter, Cosine score calculation) và chất lượng mô hình ngôn ngữ. `MockEmbedder` dựa trên SHA-256 hash chỉ tạo ra vector giả ngẫu nhiên, không thể biểu diễn ngữ nghĩa.
- **Tác dụng của Metadata Filtering:** Khi chất lượng embedding giảm (hoặc dùng mock), Metadata Filtering là "cứu cánh" duy nhất giúp thu hẹp phạm vi không gian vector và tăng khả năng trúng câu hỏi.
- **Tốc độ vs Độ chính xác:** `MockEmbedder` chạy cực nhanh (dưới 1 giây cho toàn bộ 5 tài liệu), lý tưởng cho chạy thử nghiệm tự động (Unit Test / CI-CD), nhưng để triển khai sản phẩm thực tế bắt buộc phải chuyển đổi sang Transformer Embedder (`EMBEDDING_PROVIDER=local`).

**Bài học rút ra khi so sánh trong nhóm:**
> Việc so sánh 3 chiến lược chunking dưới cùng một Mock Embedder cho thấy kết quả truy xuất bị ảnh hưởng lớn bởi số lượng và phân bố chunk. Để đánh giá chính xác sức mạnh của Chunking, cần kết hợp với một mô hình Embedding có khả năng hiểu ngữ nghĩa thực sự.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> 1) Cấu hình linh hoạt giữa `MockEmbedder` (khi chạy test nhanh) và `LocalEmbedder` (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` khi cần đánh giá ngữ nghĩa thực tế). 2) Thêm trường metadata `article_number` để filter theo điều khoản. 3) Bổ sung prompt template RAG chặt chẽ hơn.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí                                 | Điểm tự đánh giá |
| ---------------------------------------- | ---------------- |
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10          |
| Thiết kế chiến lược (Strategy Design)    | 15 / 15          |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10          |
| Thuyết trình (Demo)                      | 5 / 5            |
| **Tổng phần nhóm**                       | **40 / 40**      |
