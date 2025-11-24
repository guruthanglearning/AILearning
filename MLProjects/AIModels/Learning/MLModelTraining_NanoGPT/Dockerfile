# NanoGPT API Docker Image
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS base
WORKDIR /app
EXPOSE 8080
EXPOSE 8081

FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
ARG BUILD_CONFIGURATION=Release
WORKDIR /src

# Copy project files
COPY ["NanoGpt.Api/NanoGpt.Api.csproj", "NanoGpt.Api/"]
COPY ["NanoGpt.Core/NanoGpt.Core.csproj", "NanoGpt.Core/"]
COPY ["NanoGpt.Dashboard/NanoGpt.Dashboard.csproj", "NanoGpt.Dashboard/"]

# Restore dependencies
RUN dotnet restore "NanoGpt.Api/NanoGpt.Api.csproj"

# Copy source code
COPY . .

# Build the application
WORKDIR "/src/NanoGpt.Api"
RUN dotnet build "NanoGpt.Api.csproj" -c $BUILD_CONFIGURATION -o /app/build

# Publish the application
FROM build AS publish
ARG BUILD_CONFIGURATION=Release
RUN dotnet publish "NanoGpt.Api.csproj" -c $BUILD_CONFIGURATION -o /app/publish /p:UseAppHost=false

# Final stage/image
FROM base AS final
WORKDIR /app

# Create directories for logs and data
RUN mkdir -p /app/logs /app/data /app/checkpoints

# Copy the published application
COPY --from=publish /app/publish .

# Copy training data
COPY ["data/", "/app/data/"]

# Copy configuration
COPY ["config.json", "/app/"]

# Set environment variables
ENV ASPNETCORE_ENVIRONMENT=Production
ENV ASPNETCORE_URLS=http://+:8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Set the entry point
ENTRYPOINT ["dotnet", "NanoGpt.Api.dll"]