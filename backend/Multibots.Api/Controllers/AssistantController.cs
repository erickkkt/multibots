using Microsoft.AspNetCore.Mvc;

namespace Multibots.Api.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class AssistantController : ControllerBase
    {
        [HttpPost("chat")]
        public IActionResult Chat([FromBody] ChatRequest request)
        {
            // Implement your chat logic here
            return Ok(); // Return an appropriate response
        }
    }

    public class ChatRequest
    {
        public string Message { get; set; }
        public string UserId { get; set; }
    }
}