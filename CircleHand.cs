//This is the circle for hand
// Circle.cs
//
// This example uses a StreamingEmitter to project a ControlPoint moving
// in a circle, 20cm above the centre of the array. The radius of the
// circle can be changed during playback.
//

using System;
using System.Numerics;
using Ultraleap.Haptics;
using System.IO;
using System.Linq;
using System.Globalization;
using System.Threading;

internal class Circle
{
    public Circle(StreamingEmitter emitter)
    {
        _emitter = emitter;
        Radius = 0.012f; // 2cm
        Speed = 15.08f; // 8 metres per second

        // Set the ControlPointCount to 1, as we are only emitting 1 ControlPoint at a time
        emitter.SetControlPointCount(1, AdjustRate.AsRequired);

        // Set the callback function on the emitter
        //emitter.EmissionCallback = Callback;
    }

    public float Radius { get; set; }
    public float Speed { get; set; }

    public void Start()
    {
        _startTime = DateTimeOffset.UtcNow;
        _emitter.Start();
    }

    public void Stop()
    {
        _emitter.Stop();
    }

    private DateTimeOffset _startTime;
    private readonly StreamingEmitter _emitter;
}

internal static class Example
{
    private static void RunExample(float x, float y, float z, float frequency)
    {
        using Library lib = new Library();
        lib.Connect();

        // Find a device to use
        using IDevice device = lib.FindDevice();

        // Create an emitter
        using StreamingEmitter emitter = new StreamingEmitter(lib);

        // Add the device to the emitter
        emitter.Devices.Add(device);

        Circle circle = new Circle(emitter);

        float Radius = 0.012f; // 2cm
        float Speed = 15.08f;
        DateTimeOffset _startTime = DateTimeOffset.UtcNow;

        void Callback(
        StreamingEmitter emitter,
        StreamingEmitter.Interval interval,
        DateTimeOffset submissionDeadline)
        {
            foreach (var sample in interval)
            {
                double seconds = (sample.Time - _startTime).TotalSeconds;

                var angularVelocity = Speed / Radius;
                var phase = angularVelocity * seconds;

                // Anti-clockwise circle starting at (_radius, 0, 0.2)
                Vector3 p;
                p.X = (float)Math.Cos(phase) * Radius;
                p.Y = -(float)Math.Sin(phase) * Radius - y + 0.14f;
                p.Z = (float)z; // 20cm above the device
                float theta = 0 * (float)(Math.PI) / 180;
                //+p.Z * (float)Math.Sin(theta); +p.Z * (float)Math.Cos(theta)
                p.X = -p.X * (float)Math.Cos(theta) - x - 0.01f;
                p.Z = p.Z - p.X * (float)Math.Sin(theta) + 0.05f;

                sample.Points[0].Position = p;
                sample.Points[0].Intensity = 1.0f;
            }
        }
        emitter.EmissionCallback = Callback;

        // Begin playback
        circle.Start();
        Thread.Sleep((int)(1000 / frequency)); // Adjust the sleep time based on the frequency
        // Stop emission
        circle.Stop();
        Console.WriteLine("Stopped Emitter");
        Thread.Sleep((int)(100000 / frequency));
    }

    public static void Main(string[] args)
    {
        string csvFilePath = @".csv"; // csv path

        float frequency = 1.0f; // Frequency set to 100 times per second

        while (true)
        {
            if (File.Exists(csvFilePath))
            {
                var lastLine = File.ReadLines(csvFilePath).Last();
                string[] split = lastLine.Split(',');

                if (split.Length == 3)
                {
                    float x = float.Parse(split[0], CultureInfo.InvariantCulture);
                    float y = float.Parse(split[1], CultureInfo.InvariantCulture);
                    float z = float.Parse(split[2], CultureInfo.InvariantCulture);

                    
                    if (x != 0 || y != 0 || z != 0)
                    {
                        Console.WriteLine($"x: {x}, y: {y}, z: {z}");

                        try
                        {
                            RunExample(x, y, z, frequency);
                        }
                        catch (LibraryException e) when (e.Code == ErrorCode.LibraryNotConnected)
                        {
                            Console.WriteLine("Failed to connect to the Ultraleap Haptics service. Please check that the service is running...");
                            Console.WriteLine($"Error message: {e.Message}");
                        }
                        catch (LibraryException e) when (e.Code == ErrorCode.DeviceUnavailable)
                        {
                            Console.WriteLine("Failed to find a Device. Please check that the device is powered on and plugged in...");
                            Console.WriteLine($"Error message: {e.Message}");
                        }
                        catch (Exception e)
                        {
                            // Handle the exception
                            Console.WriteLine(e);
                        }
                    }
                }

                // Sleep for 0.5 seconds before reading the file again
                Thread.Sleep(2);
            }
            else
            {
                Console.WriteLine($"CSV file not found at path: {csvFilePath}");
                Thread.Sleep(2);
            }
        }
    }
}
