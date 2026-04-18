using Multibots.Api.Models;

namespace Multibots.Api.Services;

public interface IPythonEngineClient
{
    Task<AnalyzeResponse> AnalyzeAsync(AnalyzeRequest request, CancellationToken cancellationToken);
}
