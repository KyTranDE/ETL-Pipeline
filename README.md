# ETL-pipeline-With-Docker-compose-Redis-cache.
![image](https://github.com/user-attachments/assets/cab7f279-a407-4196-97ae-e98757171223)
### Docker Compose
- **Docker Compose** là công cụ dùng để định nghĩa và quản lý đa container Docker. Nó giúp triển khai và duy trì các dịch vụ độc lập bên trong container một cách dễ dàng.

### Service Crawl
- Dịch vụ này được cấu hình để chạy mỗi 2 giây. Nó thực hiện việc quét và thu thập dữ liệu từ webAPI.
- Dữ liệu thu thập được sau đó sẽ được chuyển tiếp để xử lý thêm.

### Data
- Sau khi dịch vụ crawl thu thập được dữ liệu, dữ liệu này sẽ được lưu trữ tạm thời trong một vùng đệm trung gian.

### Redis Cache
- **Redis** là một hệ thống lưu trữ dữ liệu trong bộ nhớ đệm, được sử dụng để tăng tốc độ truy cập dữ liệu.
- Trong hệ thống này, Redis cache có nhiệm vụ kiểm tra xem dữ liệu vừa thu thập có bị trùng lặp không.
- Redis sẽ kiểm tra các khóa (keys). Nếu phát hiện khóa trùng lặp, dữ liệu sẽ bị bỏ qua và không được cập nhật vào cơ sở dữ liệu.

### Noduplicated
- Nếu dữ liệu không bị trùng lặp (tức là không tìm thấy khóa trùng lặp trong Redis), dữ liệu sẽ được đánh dấu là "no duplicated".
- Dữ liệu "no duplicated" sẽ được chuẩn bị để chuyển tiếp sang các bước xử lý tiếp theo.

### Database Backup
- Dữ liệu đã qua kiểm tra và không bị trùng lặp sẽ được sao lưu vào cơ sở dữ liệu chính.
- Đây là bước quan trọng để đảm bảo rằng tất cả dữ liệu hợp lệ được lưu trữ một cách an toàn và có thể truy cập lại khi cần.

### Post API Web EC2
- Sau khi dữ liệu được sao lưu, nó sẽ được đăng lên một API web, được triển khai trên một instance EC2 của AWS.
- API này có thể được sử dụng để cung cấp dữ liệu để hiển thị trên web.

## Chú Thích Bổ Sung
- `Redis cache chịu trách nhiệm kiểm tra các khóa trùng lặp. Nếu tìm thấy trùng lặp, dữ liệu sẽ bị bỏ qua và không được cập nhật vào cơ sở dữ liệu. Điều này giúp đảm bảo rằng database không bị truy cập liên tục và postapi chỉ thay đổi khi data crawl về thay đổi giảm thiểu tối đa lượng request.`
- `Service crawl chạy mỗi 2 giây để đảm bảo dữ liệu được thu thập liên tục và cập nhật kịp thời gần với time thực tế.`

## Cài Đặt và Sử Dụng
- dịch vụ private (no config).

