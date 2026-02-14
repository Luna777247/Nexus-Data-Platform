# Apache Superset - BI & Data Visualization

Apache Superset integration for Nexus Data Platform

## 📊 Overview

Apache Superset là modern data exploration and visualization platform được tích hợp vào Nexus Data Platform để cung cấp:
- **Business Intelligence**: Dashboards và reports cho business users
- **Data Exploration**: Interactive exploration của Gold layer data
- **Self-Service Analytics**: Cho phép analysts tự tạo charts và dashboards
- **SQL Lab**: Advanced SQL editor với query history

---

## 🚀 Quick Start

### 1. Start Superset

```bash
# Start all services including Superset
docker-compose -f infra/docker-stack/docker-compose-production.yml up -d

# Check Superset logs
docker logs nexus-superset -f
```

### 2. Access Superset UI

**URL:** http://localhost:8088

**Default Credentials:**
- Username: `admin`
- Password: `admin123`

⚠️ **IMPORTANT:** Change default password in production!

---

## 🔌 Database Connections

Superset đã được cấu hình để kết nối với các databases trong platform:

### Add ClickHouse Connection

1. Navigate to **Data → Databases → + Database**
2. Select **ClickHouse** (or Other if not available)
3. Enter connection details:
   ```
   SQLAlchemy URI: clickhouse://default:clickhouse123@clickhouse:8123/analytics
   ```
4. Test Connection → Save

### Add PostgreSQL Connection (Iceberg Catalog)

1. Navigate to **Data → Databases → + Database**
2. Select **PostgreSQL**
3. Enter connection details:
   ```
   SQLAlchemy URI: postgresql://admin:admin123@postgres-iceberg:5432/iceberg_catalog
   ```
4. Test Connection → Save

---

## 📈 Creating Dashboards

### Step 1: Add Dataset

1. Go to **Data → Datasets → + Dataset**
2. Select database (ClickHouse or PostgreSQL)
3. Select schema and table from Gold layer:
   - `gold.user_360_view`
   - `gold.booking_metrics`
   - `gold.tourism_analytics`
4. Click **Add**

### Step 2: Create Charts

1. Go to **Charts → + Chart**
2. Select dataset
3. Select visualization type:
   - **Time Series**: For trends over time
   - **Big Number**: For KPIs
   - **Pie Chart**: For distribution
   - **Table**: For detailed data
   - **Map**: For geographical data
4. Configure metrics and filters
5. **Save** chart

### Step 3: Create Dashboard

1. Go to **Dashboards → + Dashboard**
2. Drag and drop saved charts
3. Add filters for interactivity
4. **Save** dashboard

---

## 🔍 SQL Lab Usage

### Execute SQL Queries

1. Go to **SQL Lab → SQL Editor**
2. Select database
3. Write SQL query:
   ```sql
   SELECT 
       region,
       COUNT(*) as booking_count,
       AVG(price) as avg_price
   FROM gold.booking_metrics
   WHERE booking_date >= CURRENT_DATE - INTERVAL 30 DAY
   GROUP BY region
   ORDER BY booking_count DESC
   ```
4. **Run Query**
5. **Explore** or **Visualize** results

### Save Queries

- Click **Save** to save query for later use
- Queries are saved with name and description
- Access saved queries from SQL Lab sidebar

---

## 🎨 Example Dashboards

### Tourism Analytics Dashboard

**Charts to Include:**
1. **Total Bookings (Big Number)**: Total bookings this month
2. **Revenue Trend (Line Chart)**: Daily revenue over last 30 days
3. **Regional Distribution (Pie Chart)**: Bookings by region
4. **Top Tours (Table)**: Top performing tours
5. **Booking Heatmap (Map)**: Geographic distribution of bookings

### User Engagement Dashboard

**Charts to Include:**
1. **Active Users (Big Number)**: Monthly active users
2. **User Growth (Area Chart)**: User registration trend
3. **Engagement Rate (Gauge)**: User engagement percentage
4. **Session Duration (Histogram)**: Distribution of session lengths
5. **Popular Features (Bar Chart)**: Most used features

---

## ⚙️ Configuration

### Environment Variables

Located in `docker-compose-production.yml`:

```yaml
SUPERSET_SECRET_KEY: 'nexus_superset_secret_key_change_in_production_2026'
SQLALCHEMY_DATABASE_URI: 'postgresql+psycopg2://superset:superset123@superset-postgres:5432/superset'
SUPERSET_WEBSERVER_PORT: 8088
SUPERSET_LOAD_EXAMPLES: 'no'
```

### Custom Configuration

Edit `infra/docker-stack/superset/superset_config.py` for:
- Feature flags
- Security settings
- Cache configuration
- Email alerts
- Rate limiting

---

## 🔐 Security Best Practices

### 1. Change Default Credentials

```bash
docker exec -it nexus-superset superset fab create-admin \
    --username your-admin \
    --firstname YourFirstName \
    --lastname YourLastName \
    --email your.email@company.com \
    --password your-secure-password
```

### 2. Enable HTTPS

Configure reverse proxy (Nginx/Traefik) with SSL certificate

### 3. Set Strong SECRET_KEY

Update `SUPERSET_SECRET_KEY` environment variable with strong random string

### 4. Configure RBAC

Use Superset's built-in role-based access control:
- **Admin**: Full access
- **Alpha**: Can create and edit dashboards
- **Gamma**: View-only access
- **SQL Lab**: SQL Lab access only

---

## 🔄 Data Refresh

### Automatic Cache Refresh

Configure in dataset settings:
1. Go to **Data → Datasets**
2. Edit dataset
3. Set **Cache Timeout**: 3600 (1 hour)
4. Enable **Async Query Execution** for large datasets

### Manual Refresh

- Click **Refresh** icon on dashboard
- Or set up scheduled refreshes via Celery (advanced)

---

## 📧 Email Alerts (Optional)

### Configure SMTP

Uncomment in `docker-compose-production.yml`:

```yaml
SMTP_HOST: smtp.gmail.com
SMTP_STARTTLS: 'true'
SMTP_SSL: 'false'
SMTP_USER: your-email@gmail.com
SMTP_PORT: 587
SMTP_PASSWORD: your-app-password
SMTP_MAIL_FROM: superset@nexus.com
```

### Create Alerts

1. Go to **Alerts & Reports → + Alert**
2. Configure conditions
3. Set recipients
4. Schedule delivery

---

## 🐛 Troubleshooting

### Superset won't start

```bash
# Check logs
docker logs nexus-superset

# Restart container
docker restart nexus-superset

# Rebuild if needed
docker-compose -f infra/docker-stack/docker-compose-production.yml up -d --build superset
```

### Database connection fails

```bash
# Verify database is running
docker ps | grep clickhouse
docker ps | grep postgres

# Test connection from Superset container
docker exec -it nexus-superset curl http://clickhouse:8123
docker exec -it nexus-superset pg_isready -h postgres-iceberg -U admin
```

### Can't create admin user

```bash
# Initialize database first
docker exec -it nexus-superset superset db upgrade

# Then create admin
docker exec -it nexus-superset superset fab create-admin \
    --username admin \
    --firstname Admin \
    --lastname User \
    --email admin@nexus.com \
    --password admin123
```

---

## 📚 Resources

- **Official Docs**: https://superset.apache.org/docs/intro
- **Installation Guide**: https://superset.apache.org/docs/installation/installing-superset-using-docker-compose
- **Creating Charts**: https://superset.apache.org/docs/creating-charts-dashboards/creating-your-first-dashboard
- **SQL Lab**: https://superset.apache.org/docs/creating-charts-dashboards/creating-your-first-dashboard#creating-charts-in-explore-view

---

## 🎯 Integration with Nexus Platform

### Data Sources

Superset connects to:
- ✅ **ClickHouse**: Gold layer analytics data
- ✅ **PostgreSQL**: Iceberg catalog metadata
- 🔄 **Future**: Direct Iceberg table querying

### Authentication

Can be integrated with platform RBAC:
- Use OAuth/OIDC for SSO
- Map platform roles to Superset roles
- Centralized user management

### Monitoring

Superset metrics exposed to Prometheus:
- Query performance
- Dashboard usage
- User activities
- Error rates

---

## 📊 Sample Queries

### Tourism KPIs

```sql
-- Total revenue last 30 days
SELECT SUM(total_amount) as revenue
FROM gold.booking_metrics
WHERE booking_date >= CURRENT_DATE - INTERVAL 30 DAY;

-- Top 10 destinations
SELECT 
    destination,
    COUNT(*) as bookings,
    AVG(rating) as avg_rating
FROM gold.tourism_analytics
GROUP BY destination
ORDER BY bookings DESC
LIMIT 10;

-- User retention rate
SELECT 
    cohort_month,
    retention_rate
FROM gold.user_360_view
ORDER BY cohort_month DESC;
```

---

**🎉 You're now ready to create stunning dashboards with Apache Superset!**
