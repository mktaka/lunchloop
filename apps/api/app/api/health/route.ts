export async function GET() {
  return Response.json({
    status: "ok",
    service: "lunchloop-api"
  });
}
