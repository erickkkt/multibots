FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src

COPY ["backend/Multibots.Api/Multibots.Api.csproj", "backend/Multibots.Api/"]
RUN dotnet restore "backend/Multibots.Api/Multibots.Api.csproj"

COPY . .
RUN dotnet publish "backend/Multibots.Api/Multibots.Api.csproj" -c Release -o /app/publish /p:UseAppHost=false

FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS final
WORKDIR /app
COPY --from=build /app/publish .

ENV ASPNETCORE_URLS=http://+:8080
EXPOSE 8080

ENTRYPOINT ["dotnet", "Multibots.Api.dll"]
