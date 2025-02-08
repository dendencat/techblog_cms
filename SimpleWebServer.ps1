param (
    [int]$port = 8080
)

$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://*:$port/")
$listener.Start()
Write-Output "Listening on port $port..."

while ($listener.IsListening) {
    $context = $listener.GetContext()
    $response = $context.Response
    $response.ContentType = "text/plain"
    $response.StatusCode = 200
    $response.StatusDescription = "OK"
    $buffer = [System.Text.Encoding]::UTF8.GetBytes("Hello, World!")
    $response.OutputStream.Write($buffer, 0, $buffer.Length)
    $response.Close()
}

$listener.Stop()