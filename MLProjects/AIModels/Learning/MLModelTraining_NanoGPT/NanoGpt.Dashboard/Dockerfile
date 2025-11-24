# NanoGPT Dashboard Dockerfile
FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS base
WORKDIR /app
EXPOSE 8080
EXPOSE 8081

FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src

# Copy project file
COPY ["NanoGpt.Dashboard.csproj", "."]
RUN dotnet restore "NanoGpt.Dashboard.csproj"

# Copy source code
COPY . .

# Build application
RUN dotnet build "NanoGpt.Dashboard.csproj" -c Release -o /app/build

FROM build AS publish
RUN dotnet publish "NanoGpt.Dashboard.csproj" -c Release -o /app/publish /p:UseAppHost=false

FROM base AS final
WORKDIR /app

# Copy published application
COPY --from=publish /app/publish .

# Set environment variables
ENV ASPNETCORE_ENVIRONMENT=Production
ENV ASPNETCORE_URLS=http://+:8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

ENTRYPOINT ["dotnet", "NanoGpt.Dashboard.dll"]