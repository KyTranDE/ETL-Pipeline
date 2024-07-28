# ETL-pipeline
![image](https://github.com/user-attachments/assets/cab7f279-a407-4196-97ae-e98757171223)
# Hệ Thống Quản Lý Dữ Liệu

## Giới thiệu
Đây là hệ thống quản lý dữ liệu sử dụng Docker Compose để quản lý và triển khai các container Docker, với dịch vụ crawl dữ liệu, Redis cache để kiểm tra trùng lặp, và cơ sở dữ liệu sao lưu. Dữ liệu được đăng lên một API web trên EC2 của AWS.

## Luồng Hoạt Động Chi Tiết

### Docker Compose
- **Docker Compose** là công cụ dùng để định nghĩa và quản lý đa container Docker. Nó giúp triển khai và duy trì các dịch vụ độc lập bên trong container một cách dễ dàng.

### Service Crawl
- Dịch vụ này được cấu hình để chạy mỗi 2 giây. Nó thực hiện việc quét và thu thập dữ liệu từ các nguồn khác nhau, bao gồm các trang web, API, hoặc các nguồn dữ liệu khác.
- Dữ liệu thu thập được sau đó sẽ được chuyển tiếp để xử lý thêm.

### Data
- Sau khi dịch vụ crawl thu thập được dữ liệu, dữ liệu này sẽ được lưu trữ tạm thời trong một vùng đệm hoặc bảng dữ liệu trung gian.

### Redis Cache
- **Redis** là một hệ thống lưu trữ dữ liệu trong bộ nhớ đệm, được sử dụng để tăng tốc độ truy cập dữ liệu.
- Trong hệ thống này, Redis cache có nhiệm vụ kiểm tra xem dữ liệu vừa thu thập có bị trùng lặp không.
- Redis sẽ kiểm tra các khóa (keys). Nếu phát hiện khóa trùng lặp, dữ liệu sẽ bị bỏ qua và không được cập nhật vào cơ sở dữ liệu.

### Noduplicated
- Nếu dữ liệu không bị trùng lặp (tức là không tìm thấy khóa trùng lặp trong Redis), dữ liệu sẽ được đánh dấu là "noduplicated".
- Dữ liệu "noduplicated" sẽ được chuẩn bị để chuyển tiếp sang các bước xử lý tiếp theo.

### Database Backup
- Dữ liệu đã qua kiểm tra và không bị trùng lặp sẽ được sao lưu vào cơ sở dữ liệu chính.
- Đây là bước quan trọng để đảm bảo rằng tất cả dữ liệu hợp lệ được lưu trữ một cách an toàn và có thể truy cập lại khi cần.

### Post API Web EC2
- Sau khi dữ liệu được sao lưu, nó sẽ được đăng lên một API web, được triển khai trên một instance EC2 của AWS.
- API này có thể được sử dụng để cung cấp dữ liệu cho các ứng dụng khác hoặc để hiển thị trên web.

## Chú Thích Bổ Sung
- Redis cache chịu trách nhiệm kiểm tra các khóa trùng lặp. Nếu tìm thấy trùng lặp, dữ liệu sẽ bị bỏ qua và không được cập nhật vào cơ sở dữ liệu. Điều này giúp đảm bảo rằng không có dữ liệu trùng lặp được lưu trữ, giữ cho cơ sở dữ liệu sạch sẽ và hiệu quả.
- Service crawl chạy mỗi 2 giây để đảm bảo dữ liệu được thu thập liên tục và cập nhật kịp thời.

## Cài Đặt và Sử Dụng

### Yêu Cầu
- Docker
- Docker Compose

### Hướng Dẫn Cài Đặt
1. Clone repository:
    ```sh
    git clone <repository-url>
    cd <repository-directory>
    ```

2. Khởi động các dịch vụ:
    ```sh
    docker-compose up
    ```

3. Kiểm tra các dịch vụ:
    - Dịch vụ crawl: chạy mỗi 2 giây để thu thập dữ liệu.
    - Redis cache: kiểm tra và loại bỏ dữ liệu trùng lặp.
    - Cơ sở dữ liệu: lưu trữ dữ liệu hợp lệ.
    - API web: cung cấp dữ liệu cho các ứng dụng khác.

## Đóng Góp
- Hãy gửi pull request để đóng góp vào dự án.
- Báo cáo lỗi hoặc yêu cầu tính năng mới qua mục Issues.

## Giấy Phép
- Dự án này được phát hành dưới [tên giấy phép].

