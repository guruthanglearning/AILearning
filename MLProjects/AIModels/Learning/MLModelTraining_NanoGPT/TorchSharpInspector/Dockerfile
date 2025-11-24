# TorchSharp Inspector Web Application Dockerfile
FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS base
WORKDIR /app
EXPOSE 8080
EXPOSE 8081

# Install required system packages
RUN apt-get update && apt-get install -y \
    libc6-dev \
    libgdiplus \
    libx11-dev \
    && rm -rf /var/lib/apt/lists/*

FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src

# Copy project files
COPY ["TorchSharpInspector.csproj", "TorchSharpInspector/"]
COPY ["../NanoGpt.Core/NanoGpt.Core.csproj", "NanoGpt.Core/"]

# Restore dependencies
RUN dotnet restore "TorchSharpInspector/TorchSharpInspector.csproj"

# Copy source code
COPY . TorchSharpInspector/
COPY ../NanoGpt.Core/ NanoGpt.Core/

# Build application
WORKDIR "/src/TorchSharpInspector"
RUN dotnet build "TorchSharpInspector.csproj" -c Release -o /app/build

FROM build AS publish
RUN dotnet publish "TorchSharpInspector.csproj" -c Release -o /app/publish /p:UseAppHost=false

FROM base AS final
WORKDIR /app

# Create necessary directories
RUN mkdir -p /app/logs /app/reports /app/models

# Copy published application
COPY --from=publish /app/publish .

# Set environment variables
ENV ASPNETCORE_ENVIRONMENT=Production
ENV ASPNETCORE_URLS=http://+:8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/health || exit 1

ENTRYPOINT ["dotnet", "TorchSharpInspector.dll"]