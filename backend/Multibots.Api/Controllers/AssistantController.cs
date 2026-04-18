using Microsoft.AspNetCore.Mvc;

namespace Multibots.Api.Controllers;

[Route("api/[controller]")]
[ApiController]
public class AssistantController : ControllerBase
{
    [HttpPost("chat")]
    public IActionResult Chat([FromBody] ChatRequest request)
    {
        if (string.IsNullOrWhiteSpace(request.Message))
        {
            return BadRequest("Message is required.");
        }

        return Ok(new { reply = $"Echo: {request.Message.Trim()}" });
    }
}

public class ChatRequest
{
    public string Message { get; set; } = string.Empty;
    public string UserId { get; set; } = string.Empty;
}
