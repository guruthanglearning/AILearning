# ── Stage 1: Build ───────────────────────────────────────────────────────────
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src

# Copy solution and all project files first for layer caching
COPY MultiAgentDevTeam.slnx ./
COPY NuGet.Config ./
COPY src/MultiAgentDevTeam.Shared/ src/MultiAgentDevTeam.Shared/
COPY src/MultiAgentDevTeam.Orchestrator/ src/MultiAgentDevTeam.Orchestrator/
COPY src/Agents/MultiAgentDevTeam.PMAgent/ src/Agents/MultiAgentDevTeam.PMAgent/
COPY src/Agents/MultiAgentDevTeam.ArchitectAgent/ src/Agents/MultiAgentDevTeam.ArchitectAgent/
COPY src/Agents/MultiAgentDevTeam.DeveloperAgent/ src/Agents/MultiAgentDevTeam.DeveloperAgent/
COPY src/Agents/MultiAgentDevTeam.ReviewerAgent/ src/Agents/MultiAgentDevTeam.ReviewerAgent/
COPY src/Agents/MultiAgentDevTeam.QAAgent/ src/Agents/MultiAgentDevTeam.QAAgent/
COPY src/Agents/MultiAgentDevTeam.SecurityAgent/ src/Agents/MultiAgentDevTeam.SecurityAgent/
COPY src/Agents/MultiAgentDevTeam.DevOpsAgent/ src/Agents/MultiAgentDevTeam.DevOpsAgent/
COPY src/Agents/MultiAgentDevTeam.DocsAgent/ src/Agents/MultiAgentDevTeam.DocsAgent/

# Override the Windows-specific globalPackagesFolder from NuGet.Config — that path is invalid inside Linux containers.
ENV NUGET_PACKAGES=/tmp/nuget-packages

RUN dotnet restore src/MultiAgentDevTeam.Orchestrator/MultiAgentDevTeam.Orchestrator.csproj

RUN dotnet publish src/MultiAgentDevTeam.Orchestrator/MultiAgentDevTeam.Orchestrator.csproj \
    -c Release -o /app/publish --no-restore

# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS runtime
WORKDIR /app

# Install curl for healthcheck, then drop to non-root user
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Run as non-root user for security (Debian-based image uses groupadd/useradd)
RUN groupadd --system appgroup && useradd --system --gid appgroup --no-create-home appuser
USER appuser

COPY --from=build /app/publish .

EXPOSE 5000

ENV ASPNETCORE_URLS=http://+:5000
ENV ASPNETCORE_ENVIRONMENT=Production

ENTRYPOINT ["dotnet", "MultiAgentDevTeam.Orchestrator.dll"]
