# Simple Status Server 🚀

![GitHub stars](https://img.shields.io/github/stars/cidkagenou7/simple-status-server?style=social) ![GitHub forks](https://img.shields.io/github/forks/cidkagenou7/simple-status-server?style=social) ![GitHub issues](https://img.shields.io/github/issues/cidkagenou7/simple-status-server) ![GitHub license](https://img.shields.io/github/license/cidkagenou7/simple-status-server)

Welcome to the **Simple Status Server**! This project offers a straightforward solution for monitoring the status of various services, commands, files, and URLs. With built-in logging, graphing capabilities, and a robust API, you can keep track of your systems effortlessly.

## Table of Contents

- [Features](#features)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Graphing](#graphing)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Features

- **Multi-Protocol Support**: Monitor services, commands, files, and URLs.
- **Logging**: Keep a detailed log of all status checks.
- **Graphs**: Visualize data over time with interactive graphs.
- **API**: Access status data programmatically.
- **Configurable**: Easily adjust settings to fit your needs.
- **Production Ready**: Designed for reliability in production environments.

## Getting Started

To get started with the Simple Status Server, download the latest release from our [Releases section](https://github.com/cidkagenou7/simple-status-server/releases). Follow the instructions below to set it up on your machine.

### Prerequisites

Make sure you have the following installed:

- Python 3.x
- Flask
- Waitress

You can install the necessary Python packages using pip:

```bash
pip install Flask waitress
```

### Installation

1. Download the latest release from the [Releases section](https://github.com/cidkagenou7/simple-status-server/releases).
2. Extract the files to your desired directory.
3. Navigate to the directory in your terminal.
4. Run the server using:

```bash
python app.py
```

## Usage

Once the server is running, you can access it through your web browser. The default URL is `http://localhost:5000`.

### Monitoring a Service

To monitor a service, simply configure it in the settings file. You can specify the command, file path, or URL you want to check.

### Viewing Logs

Access the logs through the `/logs` endpoint. This will give you a detailed view of all the status checks performed.

## Configuration

The Simple Status Server uses a configuration file to set up various parameters. The configuration file is in JSON format. Here’s a sample configuration:

```json
{
  "services": [
    {
      "name": "My Service",
      "type": "url",
      "value": "http://example.com",
      "interval": 60
    }
  ]
}
```

### Configuration Options

- **name**: A friendly name for the service.
- **type**: The type of service (e.g., `url`, `command`, `file`).
- **value**: The URL, command, or file path to monitor.
- **interval**: How often to check the service (in seconds).

## API Reference

The Simple Status Server offers a RESTful API to access the status of your monitored services.

### Endpoints

- **GET /status**: Returns the current status of all monitored services.
- **GET /logs**: Retrieves the logs of all status checks.
- **POST /services**: Add a new service to monitor.

### Example Request

To get the current status of all services, you can use the following command:

```bash
curl http://localhost:5000/status
```

## Graphing

Visualize your service data with built-in graphing features. The graphs provide insights into the uptime and performance of your monitored services.

### Accessing Graphs

Graphs are available at the `/graphs` endpoint. You can view the historical data for each service in a visual format.

## Contributing

We welcome contributions to the Simple Status Server! If you’d like to help, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and commit them.
4. Push your branch to your forked repository.
5. Open a pull request.

Please ensure your code follows our coding standards and includes tests where applicable.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any inquiries or support, please contact us at [support@example.com](mailto:support@example.com).

---

Thank you for checking out the Simple Status Server! We hope it serves your monitoring needs effectively. For more information, visit our [Releases section](https://github.com/cidkagenou7/simple-status-server/releases) to stay updated on the latest versions and features.