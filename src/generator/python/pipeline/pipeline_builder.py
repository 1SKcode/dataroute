from typing import Dict, List, Any, Optional, Set
from src.generator.python.pipeline.pipeline_step import PipelineStep


class PipelineBuilder:
    """Класс для построения пайплайнов из JSON-конфигурации"""
    
    def __init__(
        self,
        route_config: Dict[str, Any],
        std_functions_path: str,
        user_functions_path: Optional[str] = None
    ):
        """
        Инициализирует построитель пайплайна.
        
        Args:
            route_config: Конфигурация маршрута из JSON
            std_functions_path: Путь к стандартным функциям
            user_functions_path: Путь к пользовательским функциям
        """
        self.route_config = route_config
        self.std_functions_path = std_functions_path
        self.user_functions_path = user_functions_path
    
    def build_pipeline(self, source_name: str) -> List[PipelineStep]:
        """
        Строит пайплайн для указанного исходного поля.
        
        Args:
            source_name: Имя исходного поля
            
        Returns:
            Список шагов пайплайна
        """
        # Получаем конфигурацию пайплайна для данного поля
        route_data = self.route_config["routes"].get(source_name)
        if not route_data or not route_data.get("pipeline"):
            return []
        
        pipeline_data = route_data.get("pipeline", {})
        steps = []
        
        # Сортируем шаги по номеру
        for step_number in sorted(map(int, pipeline_data.keys())):
            step_data = pipeline_data.get(str(step_number))
            if step_data:
                step = PipelineStep(
                    step_data, 
                    step_number,
                    self.std_functions_path,
                    self.user_functions_path
                )
                steps.append(step)
        
        return steps
    
    def get_field_dependencies(self, source_name: str) -> Set[str]:
        """
        Возвращает множество зависимостей для данного поля.
        
        Args:
            source_name: Имя исходного поля
            
        Returns:
            Множество имен полей, от которых зависит данное поле
        """
        route_data = self.route_config["routes"].get(source_name)
        if not route_data:
            return set()
        
        return set(route_data.get("depends_on", []))
    
    def get_final_type_and_name(self, source_name: str) -> tuple:
        """
        Возвращает тип и имя целевого поля для данного исходного поля.
        
        Args:
            source_name: Имя исходного поля
            
        Returns:
            Кортеж (final_type, final_name)
        """
        route_data = self.route_config["routes"].get(source_name)
        if not route_data:
            return None, None
        
        return route_data.get("final_type"), route_data.get("final_name") 